"""Chunk Map widget for visualizing download progress with adaptive grid.

This widget implements Surge-style chunk map visualization:
- Adaptive downsampling: Visual blocks represent multiple actual chunks
- Fixed height grid (3-5 rows) regardless of total chunks
- Dynamic width based on terminal size
- Aggregated state: complete, downloading, partial, waiting
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rich.console import RenderableType
from rich.segment import Segment
from rich.style import Style
from rich.text import Text
from textual.widget import Widget

if TYPE_CHECKING:
    from ariatuc.core.download_manager import Download

logger = logging.getLogger(__name__)


class ChunkMap(Widget):
    """Chunk map visualization widget using adaptive grid strategy.

    Design Philosophy (from Surge):
    - NOT 1:1 mapping of chunks to visual blocks
    - Fixed visual grid size (3-5 rows × dynamic columns)
    - Aggregates multiple chunks into each visual block
    - Shows granular progress without overwhelming UI

    Visual States:
    - █ Complete (green): All chunks in this block completed
    - █ Downloading (pink): At least one chunk actively downloading
    - █ Partial (yellow): Some progress but paused
    - █ Waiting (gray): No progress yet
    """

    DEFAULT_CSS = """
    ChunkMap {
        height: auto;
        width: 100%;
        padding: 0 1;
    }
    """

    # Visual grid configuration (inspired by Surge)
    VISUAL_ROWS = 4  # Fixed rows, never grows with chunk count
    BLOCK_CHAR = "█"  # Unicode block for solid fill

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize chunk map widget.

        Args:
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self._download: Download | None = None

    def set_download(self, download: Download) -> None:
        """Set the download to visualize.

        Args:
            download: Download object with chunk/piece information
        """
        self._download = download
        self.refresh()

    def clear(self) -> None:
        """Clear the current download."""
        self._download = None
        self.refresh()

    def render(self) -> RenderableType:
        """Render the chunk map grid.

        Returns:
            Rich renderable for the chunk map
        """
        if not self._download:
            return Text("No download selected", style="dim")

        # Get download info
        total_length = self._download.total_length
        completed_length = self._download.completed_length

        # If no size info, can't render chunks
        if total_length == 0:
            return Text("Size unknown", style="dim")

        # Calculate visual grid dimensions
        terminal_width = self.size.width
        if terminal_width == 0:
            terminal_width = 60  # Fallback

        # Each visual block takes 1 character
        visual_cols = max(terminal_width - 4, 10)  # Reserve padding

        # Calculate chunks per visual block
        total_visual_blocks = self.VISUAL_ROWS * visual_cols
        # Assume typical chunk size (aria2 default: 1MB)
        # For simplicity, divide file into equal visual segments
        bytes_per_block = total_length // total_visual_blocks if total_visual_blocks > 0 else 1

        # Build grid
        lines = []
        for row in range(self.VISUAL_ROWS):
            segments = []
            for col in range(visual_cols):
                block_index = row * visual_cols + col
                # Calculate byte range for this visual block
                start_byte = block_index * bytes_per_block
                end_byte = min(start_byte + bytes_per_block, total_length)

                # Determine block state based on completed bytes
                if end_byte <= completed_length:
                    # Fully completed
                    color = "green"
                elif start_byte < completed_length < end_byte:
                    # Partially downloaded (downloading or paused)
                    if self._is_active():
                        color = "magenta"  # Pink/magenta for downloading
                    else:
                        color = "yellow"  # Yellow for partial but paused
                else:
                    # Not started
                    color = "bright_black"  # Gray

                segments.append(Segment(self.BLOCK_CHAR, Style(color=color)))

            lines.append(Text.from_markup("".join(s.text for s in segments)))

        # Add progress percentage above grid
        percentage = (completed_length / total_length * 100) if total_length > 0 else 0
        header = Text(f"Download Progress: {percentage:.1f}%", style="bold")

        # Combine header and grid
        result = Text()
        result.append_text(header)
        result.append("\n")
        for line in lines:
            result.append_text(line)
            result.append("\n")

        return result

    def _is_active(self) -> bool:
        """Check if download is actively downloading.

        Returns:
            True if download is active
        """
        if not self._download:
            return False

        from ariatuc.core.download_manager import DownloadStatus

        return self._download.status == DownloadStatus.ACTIVE
