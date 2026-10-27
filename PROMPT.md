Act as an embedded-systems engineer helping me build a personal remote-control gateway for my Bose CineMate Digital Home Theater speaker system and its original remote.

Goal:
Use the remote’s AUX mode to send commands to a Raspberry Pi Pico, then translate those button presses into ordinary USB keyboard or media-key input for my computer. I want to control normal browser actions while using streaming websites—for example, navigation, select, back, play/pause, and volume. Do not assume that a streaming service has a supported API or that its controls work identically in every browser.

Use the supplied Bose CineMate Digital Home Theater manual as your primary source for product-specific facts. Analyze any relevant remote-control, AUX, programming, and device-code sections.

Important constraints:
- Do not invent IR protocols, device codes, button functions, or programming steps. Clearly label what the manual confirms, what must be tested, and what remains unknown.
- Explain that AUX may select a device profile, and may not represent one fixed set of Bose IR commands. Identify what the manual says about programming the remote for AUX and whether its instructions apply to this exact remote.
- Do not confuse codes for programming another brand’s remote to operate Bose equipment with codes used to program the Bose remote to control an AUX device.
- Prefer receiving and decoding the original remote’s IR signals; do not propose transmitting commands unless there is a clear reason.
- Keep this to controlling my own equipment and sending ordinary user-input events. Do not bypass DRM, automate account access, evade website restrictions, or interfere with other devices.

Please produce:
1. A concise summary of what the manual establishes about this remote and AUX mode, with page numbers or section names where available.
2. A recommended test plan to see whether AUX mode sends IR signals, identify the protocol or raw timings, and capture each button reliably. Include repeat/long-press handling and a way to distinguish the same button in different remote modes.
3. A simple hardware plan for a Pico-based IR receiver and USB connection. State which details depend on the exact Pico board and IR receiver module; do not assume pinouts or electrical levels without checking their documentation.
4. A proposed button-to-computer action map, clearly marked as an example that I can change. Prefer standard keyboard/media-key events over browser-specific automation.
5. A small, maintainable firmware architecture and host-side setup plan. Explain whether the Pico should appear as a USB HID keyboard/media controller or send events over USB serial to a computer program, and recommend one for a beginner.
6. A troubleshooting checklist covering missed IR signals, repeated presses, key focus, browser compatibility, and avoiding accidental system shortcuts.
7. A short list of the remaining information you need from me, such as the exact remote model or a photo of its label, the Pico board model, and my computer operating system.

Start with the manual’s verified facts. Then give the practical plan, separating confirmed facts from assumptions and experiments.
