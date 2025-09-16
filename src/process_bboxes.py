from textractor.entities.document import Document
from textractor.entities.layout import Layout


def convert_bbox(region: Layout) -> tuple[float, float, float, float]:
    x_min = region.bbox.x
    y_min = region.bbox.y
    x_max = region.bbox.x + region.bbox.width
    y_max = region.bbox.y + region.bbox.height
    return (x_min, y_min, x_max, y_max)


def bboxes_overlaps(region1: Layout, region2: Layout) -> bool:
    """
    Check if two regions overlap.

    Args:
        region1 (Layout): A region from amazon textract document.
        region2 (Layout): A region from amazon textract document.

    Returns:
        True if regions overlap, False otherwise.
    """
    x_min_1, y_min_1, x_max_1, y_max_1 = convert_bbox(region1)
    x_min_2, y_min_2, x_max_2, y_max_2 = convert_bbox(region2)

    return not (
        x_max_1 < x_min_2  # box1 is left of box2
        or x_min_1 > x_max_2  # box1 is right of box2
        or y_max_1 < y_min_2  # box1 is above box2
        or y_min_1 > y_max_2  # box1 is below box2
    )


class TextractPostProcessingBBoxes:
    """
    Class that takes Amazon Textract result for document and compares all layout bounding boxes for overlaps
    between them. List of skip ids is created during process
    """

    def __init__(self, result: Document) -> None:
        """
        Initialize the class with Amazon Textract document.

        Args:
            result (Document): Document containing regions with bounding boxes and their scores.
        """
        self.result: Document = result

    def get_list_of_skipping_ids(self) -> list[str]:
        """
        Processes Amazon Textract Document region's bounding boxes (bboxes):
        - group overlaps according to which bounding box (bbox) touches which bbox
        - inside group take bbox with highest score and remove all touching bboxes
        - repeat till all bboxes from group are processed

        Returns:
            List of region ids which to skip.
        """
        overlaps: list[tuple[int, int]] = self._find_overlaps()
        overlapping_bboxes_set: set[int] = self._convert_overlaps_to_set(overlaps)
        groups: list[set[int]] = self._group_overlaps(overlapping_bboxes_set, overlaps)
        removing: set[int] = self._get_removing_indexes(groups, overlaps)
        skipping: list[str] = []
        for index in removing:
            skipping.append(self.result.layouts[index].id)
        return skipping

    def _find_overlaps(self) -> list[tuple[int, int]]:
        """
        Create list of tupples which bounding boxes (bboxes) overlaps. Each tupple is unique.

        Returns:
            Unique list of all tupples that overlaps.
        """
        overlaps: list[tuple[int, int]] = []
        number_bboxes = len(self.result.layouts)  # Ensure there are boxes to process

        # print("Overlaps:")
        for index1 in range(number_bboxes):
            for index2 in range(index1 + 1, number_bboxes):
                if self._is_overlapping(index1, index2):
                    overlaps.append((index1, index2))
                    # # For debugging
                    # box1: Layout = self.result.layouts[index1]
                    # box2: Layout = self.result.layouts[index2]
                    # box1_debug_string: str = f"({box1.layout_type} {int(box1.confidence * 100)}%"
                    # box2_debug_string: str = f"({box2.layout_type} {int(box2.confidence * 100)}%"
                    # print(f"({box1_debug_string}, {box2_debug_string})")

        return overlaps

    def _is_overlapping(self, index1: int, index2: int) -> bool:
        """
        Check if two bounding boxes overlap.

        Args:
            index1 (int): Index of the first bounding box.
            index2 (int): Index of the second bounding box.

        Returns:
            True if the bounding boxes overlap, False otherwise.
        """
        return bboxes_overlaps(self.result.layouts[index1], self.result.layouts[index2])

    def _bboxes_overlaping_percentages(self, index1: int, index2: int) -> tuple:
        """
        Calculate the overlap percentage between two bounding boxes.

        Args:
            index1 (int): Index of the first bounding box.
            index2 (int): Index of the second bounding box.

        Returns:
            First value is percent (0-100) how much first bounding box has in overlaping area.
            Second value is percent (0-100) how much second bounding box has in overlaping area.
        """
        region1: Layout = self.result.layouts[index1]
        region2: Layout = self.result.layouts[index2]

        def bbox_size(region: Layout) -> float:
            """
            Calculate the size of a region's bounding box (bbox).

            Args:
                region (Layout): A region from amazon textract document.

            Returns:
                Size of the bbox.
            """
            x_min, y_min, x_max, y_max = convert_bbox(region)
            return max(0, x_max - x_min) * max(0, y_max - y_min)

        area_1: float = bbox_size(region1)
        area_2: float = bbox_size(region2)

        def bboxes_intersection_size(region_1: Layout, region_2: Layout) -> float:
            """
            Calculate the intersection size of two region's bounding boxes.

            Args:
                region_1 (Layout): A region from amazon textract document.
                region_2 (Layout): A region from amazon textract document.

            Returns:
                Size of intersection.
            """
            x_min_1, y_min_1, x_max_1, y_max_1 = convert_bbox(region_1)
            x_min_2, y_min_2, x_max_2, y_max_2 = convert_bbox(region_2)

            x_overlap = max(0, min(x_max_1, x_max_2) - max(x_min_1, x_min_2))
            y_overlap = max(0, min(y_max_1, y_max_2) - max(y_min_1, y_min_2))

            return x_overlap * y_overlap

        intersect_area = bboxes_intersection_size(region1, region2)

        percent1 = (intersect_area / area_1) * 100 if area_1 > 0 else 0
        percent2 = (intersect_area / area_2) * 100 if area_2 > 0 else 0

        return percent1, percent2

    def _convert_overlaps_to_set(self, overlaps: list[tuple[int, int]]) -> set[int]:
        """
        From list of tupples create set of index.

        Args:
            overlaps (list[tuple[int, int]]): Unique list of all tupples that overlaps.

        Return:
            Set of bbox indexes that overlaps with some other bbox.
        """
        return {i for pair in overlaps for i in pair}

    def _get_group_index(self, searching: int, all_groups: list[set[int]]) -> int:
        """
        Find index of group that contain searching element.

        Args:
            searching (int): Index of bbox we are searching for.
            all_groups (list[set[int]]): Currently built groups that contain set of indexes.

        Returns:
            Index if found, -1 otherwise.
        """
        return next((i for i, group in enumerate(all_groups) if searching in group), -1)

    def _group_overlaps(self, overlapping_bboxes_set: set[int], overlaps: list[tuple[int, int]]) -> list[set[int]]:
        """
        Create disjointed groups that contain indexes of bboxes that touches themselves directly or through multiple
        bboxes.

        Args:
            overlapping_bboxes_set (set[int]): Set of bbox indexes that overlaps with some other bbox.
            overlaps (list[tuple[int, int]]): Unique list of all tupples that overlaps.

        Returns:
            List of groups, where each group contain set of bbox indexes that overlaps either directly or through some
            other bbox(es).
        """
        groups: list[set[int]] = []
        for box_index in overlapping_bboxes_set:
            # Find group if exists or create new
            group_index: int = self._get_group_index(box_index, groups)
            group: set[int] = groups[group_index] if group_index >= 0 else set()

            # Fill touching members into group that are not already there:
            for index1, index2 in overlaps:
                if box_index == index1:
                    group.add(index2)
                if box_index == index2:
                    group.add(index1)

            # Save group
            if group_index < 0:
                groups.append(group)
            else:
                groups[group_index] = group

        # Merge groups that have any member in intersection
        remove_group_indexes = []
        unique_groups = []
        for group_index1 in range(len(groups)):
            if group_index1 in remove_group_indexes:
                continue
            group1 = groups[group_index1]
            for group_index2 in range(group_index1 + 1, len(groups)):
                if group_index2 in remove_group_indexes:
                    continue
                group2 = groups[group_index2]
                if group1.intersection(group2):
                    group1 = group1.union(group2)
                    remove_group_indexes.append(group_index2)
            unique_groups.append(group1)

        # # For debugging
        # print("Found groups:")
        # for group in groups:
        #     print("Group:")
        #     for member_index in group:
        #         box: Layout = self.result.layouts[member_index]
        #         print(f"{box.layout_type} {round(box.confidence * 100)}%    {convert_bbox(box)}")

        # Return disjoint sets
        return unique_groups

    def _indexes_that_can_be_merged(self, groups: list[set[int]]) -> tuple[int, int]:
        groups_size = len(groups)
        for index1 in range(groups_size):
            group1 = groups[index1]
            for index2 in range(index1 + 1, groups_size):
                group2 = groups[index2]
                if group1 & group2:
                    return index1, index2
        return -1, -1

    def _get_removing_indexes(self, groups: list[set[int]], overlaps: list[tuple[int, int]]) -> set[int]:
        """
        Process each group and gather removing indexes from each group.

        Args:
            groups (list[set[int]]): List of groups, where each group contains set of bbox indexes that overlaps either
                directly or through some other bbox(es).
            overlaps (list[tuple[int, int]]): Unique list of all tupples that overlaps.

        Returns:
            Set of indexes that should be removed.
        """
        remove_indexes: set[int] = set()

        for group in groups:
            removed = self._process_group(group, overlaps)
            remove_indexes = remove_indexes.union(removed)
            # # For debugging
            # print("Removing:")
            # for index in removed:
            #     box: Layout = self.result.layouts[index]
            #     print(f"{box.layout_type} {round(box.confidence * 100)}%")

        # # For debugging
        # print("All Removing:")
        # for index in remove_indexes:
        #     box: Layout = self.result.layouts[index]
        #     print(f"{box.layout_type} {round(box.confidence * 100)}%")

        return remove_indexes

    def _process_group(self, group: set[int], overlaps: list[tuple[int, int]]) -> set[int]:
        """
        Process members of group:
        - take highest score members
        - remove all its direct neighbours
        - repeat till all members are processed

        Args:
            group (set[int]): Group containing set of bbox indexes that overlaps either directly
                or through some other bbox(es).
            overlaps (list[tuple[int, int]]): Unique list of all tupples that overlaps.

        Returns:
            Set of indexes that should be removed.
        """
        removed: set[int] = set()
        while group:
            # Find highest score
            max_score: int = max(group, key=lambda x: float(self.result.layouts[x].confidence))

            to_further_process: set[int] = set()
            for member in group:
                if member == max_score:
                    # We are using higher score
                    pass
                elif self._is_direct_neightbour(max_score, member, overlaps):
                    # Remove direct neighbours
                    removed.add(member)
                else:
                    # Rest keep for next processing round
                    to_further_process.add(member)
            group = to_further_process

        return removed

    def _is_direct_neightbour(self, max_score_index: int, member_index: int, overlaps: list[tuple[int, int]]) -> bool:
        """
        Check if two members overlap directly.

        Args:
            max_score_index (int): Member of group that has highest score.
            member_index (int): Member we want to check if it is neighbour.
            overlaps (list[tuple[int, int]]): Unique list of all tupples that overlaps.

        Returns:
            True if bboxes overlaps.
        """
        for index1, index2 in overlaps:
            if index1 == max_score_index and index2 == member_index:
                return True
            if index1 == member_index and index2 == max_score_index:
                return True
        return False
