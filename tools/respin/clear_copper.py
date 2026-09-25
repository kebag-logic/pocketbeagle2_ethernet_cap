from kipy import KiCad

k = KiCad(socket_path="ipc:///tmp/kicad/api.sock")
b = k.get_board()
assert b.name == "pocketbeagle2_ethernet_cap.kicad_pcb", b.name
items = list(b.get_tracks()) + list(b.get_vias()) + list(b.get_zones())
print("removing", len(items), "footprints kept:", len(b.get_footprints()))
c = b.begin_commit()
b.remove_items(items)
b.push_commit(c, "Rev B re-spin: clear tracks, vias and zones")
print("after: tracks", len(b.get_tracks()), "vias", len(b.get_vias()),
      "zones", len(b.get_zones()), "fps", len(b.get_footprints()))
