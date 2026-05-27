from typing_extensions import override

from comfy_api.latest import ComfyExtension

from .hildegard_refiner import (
    Hildegard_Plan,
    Hildegard_Combine,
    Hildegard_References_Split,
)


class SteudioExtension(ComfyExtension):
    @override
    async def get_node_list(self):
        return [
            Hildegard_Plan,
            Hildegard_References_Split,
            Hildegard_Combine,
        ]


async def comfy_entrypoint() -> SteudioExtension:
    return SteudioExtension()
