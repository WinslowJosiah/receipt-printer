import textwrap
from typing import Literal, Union

from escpos.escpos import Escpos


# HACK This code is mostly taken directly from the python-escpos GitHub.
# For some reason, software_columns isn't in the version of this library
# on PyPI yet, even though it's in the GitHub and documentation.
Alignment = Union[Literal["center", "left", "right"], str]


class EscposWithSoftwareColumns(Escpos):
    @staticmethod
    def _padding(
        text: str,
        width: int,
        align: Alignment = "center",
    ) -> str:
        """Add fill space to meet the width.

        The align parameter sets the alignment of the text in space.
        """
        align = align.lower()
        if align == "center":
            text = f"{text:^{width}}"
        elif align == "left":
            text = f"{text:<{width}}"
        elif align == "right":
            text = f"{text:>{width}}"

        return text

    @staticmethod
    def _truncate(text: str, width: int, placeholder: str = ".") -> str:
        """Truncate an string at a max width or leave it untouched.

        Add a placeholder at the end of the output text if it has been truncated.
        """
        ph_len = len(placeholder)
        max_len = width - ph_len
        return f"{text[:max_len]}{placeholder}" if len(text) > width else text

    @staticmethod
    def _repeat_last(iterable, max_iterations: int = 1000):
        """Iterate over the items of a list repeating the last one until max_iterations."""
        i = 0
        while i < max_iterations:
            try:
                yield iterable[i]
            except IndexError:
                yield iterable[-1]
            i += 1

    def _rearrange_into_cols(self, text_list: list, widths: list[int], break_long_words: bool = False) -> list:
        """Wrap and convert a list of strings into an array of text columns.

        Set the width of each column by passing a list of widths.
        Wrap if possible and|or truncate strings longer than its column width.
        Reorder the wrapped items into an array of text columns.
        """
        n_cols = len(text_list)
        wrapped = [
            # HACK I'm replacing the normal textwrap with a better one
            # that respects newlines.
            "\n".join(
                "\n".join(
                    textwrap.wrap(
                        line, widths[i], break_long_words=break_long_words,
                    )
                )
                for line in text.splitlines()
                if line.strip()
            ).splitlines()
            for i, text in enumerate(text_list)
        ]
        max_len = max(*[len(text_group) for text_group in wrapped])
        text_colums = []
        for i in range(max_len):
            row = ["" for _ in range(n_cols)]
            for j, item in enumerate(wrapped):
                if i in range(len(item)):
                    row[j] = self._truncate(item[i], widths[j])
            text_colums.append(row)
        return text_colums

    def _add_padding_into_cols(
        self,
        text_list: list[str],
        widths: list[int],
        align: list[Alignment],
    ) -> list:
        """Add padding, width and alignment into the items of a list of strings."""
        return [
            self._padding(text, widths[i], align[i]) for i, text in enumerate(text_list)
        ]

    def software_columns(
        self,
        text_list: list,
        widths: Union[list[int], int],
        align: Union[list[Alignment], Alignment],
        break_long_words: bool = False,
    ) -> None:
        """Print a list of strings arranged horizontally in columns.

        :param text_list: list of strings, each item in the list will be printed as a column.

        :param widths: width of each column by passing a list of widths,
            or a single total width to arrange columns of the same size.
            If the list of width items is shorter than the list of strings then
            the last width of the list will be applied till the last string (column).

        :param align: alignment of the text into each column by passing a list of alignments,
            or a single alignment for all the columns.
            If the list of alignment items is shorter than the list of strings then
            the last alignment of the list will be applied till the last string (column).
        """
        n_cols = len(text_list)

        if isinstance(widths, int):
            widths = [round(widths / n_cols)]
        widths = list(self._repeat_last(widths, max_iterations=n_cols))

        if isinstance(align, str):
            align = [align]
        align = list(self._repeat_last(align, max_iterations=n_cols))

        columns = self._rearrange_into_cols(text_list, widths, break_long_words=break_long_words)
        for row in columns:
            padded = self._add_padding_into_cols(row, widths, align)
            self.textln("".join(padded))
