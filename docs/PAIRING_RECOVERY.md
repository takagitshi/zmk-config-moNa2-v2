# moNa2 Bluetooth pairing recovery

The normal `firmware` download contains three files:

- `mona2-left-peripheral.uf2` for the left peripheral half.
- `mona2-right-central.uf2` for the right central half.
- `mona2-pairing-reset-use-only-when-needed.uf2` for an explicit bond reset.

Write each file only to its named half. Never write the right-central image to
the left half or the left-peripheral image to the right half.

Do not use the pairing-reset image for an ordinary keymap update. It erases the
saved bonds, so an existing macOS entry will no longer reconnect afterward.

Use `mona2-pairing-reset-use-only-when-needed.uf2` only for a full pairing
recovery. Apply it to both halves, then restore the current
known-good left-peripheral image and install the current right-central image.
Power the left half on first and the right half second. On the Setting layer
run `BT_CLR_ALL`, then `BT_SEL 0`.
Remove the stale `mona2` entry from macOS Bluetooth settings and pair the newly
advertised `mona2` device once.

The reset step deliberately removes the keyboard-side bond; removing the stale
host entry is therefore part of the same recovery operation, not a normal
requirement for later firmware updates.
