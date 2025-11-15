from ha_template.ports import PortAllocator


def test_port_allocator_prefers_first_free_port():
    checked = []

    def checker(port: int) -> bool:
        checked.append(port)
        return port in {8125, 8126}

    allocator = PortAllocator(start=8123, end=8127, checker=checker)
    port = allocator.allocate(reserved=[8125])
    assert port == 8126
    assert checked[-1] == 8126
