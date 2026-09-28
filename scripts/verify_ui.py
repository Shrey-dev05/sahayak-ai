with open("frontend-kiosk/index.html", "r", encoding="utf-8") as f:
    kiosk = f.read()

assert 'meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"' in kiosk
assert "@media (max-width: 768px), (orientation: portrait)" in kiosk
assert "@media (max-height: 480px) and (orientation: landscape)" in kiosk
for cls in [".kiosk-card-heading", ".kiosk-step-row", ".kiosk-step-icon", ".step-check", ".step-doc", ".step-warn", ".step-phone", ".kiosk-alert-tag", ".kiosk-phone-pill"]:
    assert cls in kiosk, f"Missing {cls} in kiosk"
assert "function formatRichSolution(raw, lang)" in kiosk
for cls in [".hero-qr-badge-card", ".hero-qr-card-inner", ".hero-qr-canvas-box", ".hero-qr-info", ".hero-qr-pill-tag", ".hero-qr-heading"]:
    assert cls in kiosk, f"Missing {cls} in kiosk"
assert 'id="heroQrCard"' in kiosk
assert 'id="heroQrCode"' in kiosk
assert 'function showHeroQrCode(joinUrl)' in kiosk
assert "setRobotState('speaking');" in kiosk
print("✅ Frontend Kiosk Speech Output & Below-Bot QR Verification Passed!")

with open("frontend-mobile/index.html", "r", encoding="utf-8") as f:
    mob = f.read()

for cls in [".bubble .kiosk-card-heading", ".bubble .kiosk-step-row", ".bubble .kiosk-step-icon", ".bubble .step-check", ".bubble .step-doc", ".bubble .step-warn", ".bubble .step-phone", ".bubble .kiosk-alert-tag", ".bubble .kiosk-phone-pill"]:
    assert cls in mob, f"Missing {cls} in mobile"
assert "function formatRichSolution(raw, lang)" in mob
assert "formatRichSolution(text, lang)" in mob

# Mobile Dashboard UI & English/Hindi Translate Button Assertions
for cls in [".lang-toggle-btn", ".micro-card-title-row", ".check-progress-pill", ".helpline-grid", ".phone-chip-left", ".phone-chip-icon", ".phone-chip-info", ".phone-chip-title", ".phone-chip-sub", ".call-badge", ".quick-chip-row", ".quick-chip"]:
    assert cls in mob, f"Missing {cls} in mobile CSS"

# GIGW 3.0 Government Portal & Accessibility Assertions
for cls in [".tricolor-bar", ".skip-link", ".gov-masthead", ".gov-identity", ".gov-access-bar", ".access-btn", ".contrast-btn", ".portal-header", ".emblem-wrap", ".emblem-svg", ".portal-title-block", ".portal-name", ".digital-india-badge", ".grievance-track-card", ".track-id-badge", ".track-status-pill", ".track-meta-grid", ".gov-footer", ".footer-links", ".footer-compliance", ".compliance-chip", ".footer-copy", ".footer-updated", "body.high-contrast"]:
    assert cls in mob, f"Missing GIGW 3.0 class {cls} in mobile"

assert 'id="mobiLangBtn"' in mob, "Missing mobiLangBtn"
assert 'id="docProgressBadge"' in mob, "Missing docProgressBadge"
assert 'id="fontSizeDec"' in mob, "Missing fontSizeDec"
assert 'id="fontSizeNormal"' in mob, "Missing fontSizeNormal"
assert 'id="fontSizeInc"' in mob, "Missing fontSizeInc"
assert 'id="contrastToggle"' in mob, "Missing contrastToggle"
assert 'id="mainContent"' in mob, "Missing mainContent anchor"
assert "सत्यमेव जयते" in mob, "Missing Satyameva Jayate State Emblem text"
assert "Jan Samadhan" in mob, "Missing Jan Samadhan portal name"
assert "जन समाधान" in mob, "Missing Hindi Jan Samadhan portal name"
assert "setFontScale" in mob, "Missing setFontScale function"
assert "toggleHighContrast" in mob, "Missing toggleHighContrast function"
assert "function renderDashboard()" in mob, "Missing renderDashboard function"
assert "DEFAULT_PLANS" in mob, "Missing DEFAULT_PLANS definition"
assert "currentMobileLang = (currentMobileLang === 'hi') ? 'en' : 'hi';" in mob, "Missing English/Hindi toggle logic"
assert "localStorage.setItem('sahayak_mobile_lang', currentMobileLang);" in mob, "Missing language preference persistence"
assert "updateProgressBadge" in mob, "Missing updateProgressBadge function"
assert "data-query=" in mob, "Missing data-query attributes on quick chips"
assert "generateActionGuidePDF" in mob, "Missing generateActionGuidePDF function"

# Professional SVG & Emoji-Free Verification
assert '🎤' not in mob, "Karaoke mic emoji should not be present"
for svg_cls in [".mic-svg", ".section-hdr-svg", ".tool-btn-svg", ".action-btn-svg", ".warning-svg", ".phone-svg"]:
    assert svg_cls in mob, f"Missing SVG class {svg_cls} in mobile"

import re
util_match = re.search(r'id="utilitiesSection"[\s\S]*?id="actionGuideCard"', mob)
assert util_match, "utilitiesSection not found"
for bad in ['⚖️', '⚖', '📷', '✍️', '✍']:
    assert bad not in util_match.group(0), f"Found emoji {bad} in utilitiesSection"

warn_match = re.search(r'class="warning-box"[\s\S]*?</div>\s*</div>', mob)
assert warn_match, "warning-box not found"
assert '⚠️' not in warn_match.group(0) and '⚠' not in warn_match.group(0), "Found warning emoji in warning box"

print("✅ Frontend Mobile Dashboard & GIGW 3.0 Government Portal Verification Passed!")
print("ALL CHECKS PASSED SUCCESSFULLY!")

