# moNa2 Bluetooth pairing recovery

The normal keymap-only update uses only these two files:

1. `mona2-left-peripheral.uf2` on the left half.
2. `mona2-right-central-coropit.uf2` on the right half.

Do not use the pairing-reset image for an ordinary keymap update. It erases the
saved bonds, so an existing macOS entry will no longer reconnect afterward.

Use the separately built `mona2-pairing-reset-use-only-when-needed.uf2` only for
a full pairing recovery. Apply it to both halves, then install the matching
left-peripheral and right-central firmware. Power the left half on first and the
right half second. On the Setting layer run `BT_CLR_ALL`, then `BT_SEL 0`.
Remove the stale `mona2` entry from macOS Bluetooth settings and pair the newly
advertised `mona2` device once.

The reset step deliberately removes the keyboard-side bond; removing the stale
host entry is therefore part of the same recovery operation, not a normal
requirement for later firmware updates.
