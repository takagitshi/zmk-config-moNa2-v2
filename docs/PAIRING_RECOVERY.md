# moNa2 Bluetooth pairing recovery

The normal keymap, pointer, and behavior update uses only this file:

- `mona2-right-central.uf2` on the right central half.

The left peripheral is still built inside the generated-contract CI job to
detect split compatibility regressions, but it is not published because these
changes do not alter its firmware contract.

Do not use the pairing-reset image for an ordinary keymap update. It erases the
saved bonds, so an existing macOS entry will no longer reconnect afterward.

Use the manually dispatched `mona2-pairing-reset-use-only-when-needed.uf2` only
for a full pairing recovery. Apply it to both halves, then restore the last
known-good left-peripheral image and install the current right-central image.
Power the left half on first and the right half second. On the Setting layer
run `BT_CLR_ALL`, then `BT_SEL 0`.
Remove the stale `mona2` entry from macOS Bluetooth settings and pair the newly
advertised `mona2` device once.

The reset step deliberately removes the keyboard-side bond; removing the stale
host entry is therefore part of the same recovery operation, not a normal
requirement for later firmware updates.
