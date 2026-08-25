import sys
import os
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add repo root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.identity import identity
import ui

def test_onboarding_navigation():
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 1. Test SetupOverlay Initialization
    overlay = ui.SetupOverlay(defaults={})
    
    # Check page attributes exist
    assert hasattr(overlay, "_stage1_page"), "Missing _stage1_page"
    assert hasattr(overlay, "_stage_identity_page"), "Missing _stage_identity_page"
    assert hasattr(overlay, "_stage_owner_page"), "Missing _stage_owner_page"
    assert hasattr(overlay, "_stage_behavior_page"), "Missing _stage_behavior_page"
    assert hasattr(overlay, "_stage_shared_page"), "Missing _stage_shared_page"
    assert hasattr(overlay, "_stage2_page"), "Missing _stage2_page"
    assert hasattr(overlay, "_stage3_page"), "Missing _stage3_page"
    assert hasattr(overlay, "_stage4_page"), "Missing _stage4_page"
    
    print("[TEST 1 PASSED] All 8 onboarding pages created and mapped to explicit widget references.")

    # 2. Test Fresh Setup Transition
    identity.set_owner_name("")  # Simulate fresh install with no owner name
    overlay._goto_page(overlay._stage1_page, record_history=False)
    assert overlay._stack.currentWidget() == overlay._stage1_page
    
    overlay._finish_stage1()
    assert overlay._stack.currentWidget() == overlay._stage_identity_page, f"Expected identity page, got {overlay._stack.currentWidget()}"
    print("[TEST 2 PASSED] Fresh install: System Check finishes -> moves to Assistant Identity page.")

    # 3. Test Linear Navigation
    overlay._save_identity_and_next()
    assert overlay._stack.currentWidget() == overlay._stage_owner_page, "Expected owner page"
    
    overlay._save_owner_and_next()
    assert overlay._stack.currentWidget() == overlay._stage_behavior_page, "Expected behavior page"
    
    overlay._save_behavior_and_next()
    assert overlay._stack.currentWidget() == overlay._stage_shared_page, "Expected shared computer page"
    
    overlay._save_shared_and_next(False)
    assert overlay._stack.currentWidget() == overlay._stage2_page, "Expected provider selection page"
    print("[TEST 3 PASSED] Identity -> Owner -> Behavior -> Shared -> Provider Selection navigation is linear and correct.")

    # 4. CRITICAL REGRESSION TEST: Click "Connect Gemini" on Provider Selection (Stage 2)
    overlay._goto_stage3()
    assert overlay._stack.currentWidget() == overlay._stage3_page, (
        f"CRITICAL BUG REAPPEARED! 'Connect Gemini' navigated to {overlay._stack.currentWidget()} instead of _stage3_page!"
    )
    assert overlay._stack.currentWidget() != overlay._stage_identity_page, "REGRESSION: Navigated back to Assistant Identity!"
    assert overlay._stack.currentWidget() != overlay._stage_owner_page, "REGRESSION: Navigated back to Owner Profile!"
    print("[TEST 4 PASSED] Clicking 'Connect Gemini' navigates to API Key Input (_stage3_page), NOT back to Identity or Owner!")

    # 5. Test Back Button navigation from API Key Input
    overlay._go_back()
    assert overlay._stack.currentWidget() == overlay._stage2_page, "Back from API key input should return to Provider Selection"
    
    overlay._go_back()
    assert overlay._stack.currentWidget() == overlay._stage_shared_page, "Back from Provider Selection should return to Shared Computer"
    
    overlay._go_back()
    assert overlay._stack.currentWidget() == overlay._stage_behavior_page, "Back from Shared Computer should return to Assistant Behavior"
    print("[TEST 5 PASSED] Back button navigation pops history correctly and never jumps to wrong slides.")

    # 6. Test Start Ignition navigation
    overlay._goto_page(overlay._stage3_page)
    overlay._start_ignition()
    assert overlay._stack.currentWidget() == overlay._stage4_page, f"Ignition should navigate to _stage4_page, got {overlay._stack.currentWidget()}"
    print("[TEST 6 PASSED] Starting Ignition navigates to Neural Link Ignition (_stage4_page), NOT back to Behavior or Identity!")

    # 7. Test Setup Complete Skip
    identity.set_owner_name("Ravit")  # Mark setup complete
    overlay._finish_stage1()
    assert overlay._stack.currentWidget() == overlay._stage2_page, "Completed identity should jump straight to AI Provider page"
    print("[TEST 7 PASSED] Completed identity skips identity screens on System Check completion.")

    # 8. Test Dynamic Sidebar & App Identity Refresh
    win = ui.MainWindow(face_path="")
    identity.set_assistant_name("Jarvis")
    identity.set_application_name("Jarvis Core")
    win._refresh_sidebar_identity()
    text = win._sidebar_title_lbl.text()
    assert "JARVIS" in text and "CORE" in text, f"Expected JARVIS and CORE in sidebar title, got {text}"
    assert win._nav_items["home"]._lbl.text() == "Jarvis Home", f"Expected 'Jarvis Home' nav text, got {win._nav_items['home']._lbl.text()}"
    assert win._center_title_lbl.text() == "JARVIS CORE", f"Expected JARVIS CORE in center title, got {win._center_title_lbl.text()}"
    assert win._center_badge_lbl.text() == "JARVIS CORE", f"Expected JARVIS CORE in center badge, got {win._center_badge_lbl.text()}"
    assert "Ask Jarvis" in win._input.placeholderText(), f"Expected 'Ask Jarvis' in input placeholder, got {win._input.placeholderText()}"
    print("[TEST 8 PASSED] MainWindow sidebar brand header, home nav text, center badges, and input placeholders update dynamically!")

    print("\n==========================================")
    print("ALL ONBOARDING & SIDEBAR TESTS PASSED! SUCCESS!")
    print("==========================================\n")

if __name__ == "__main__":
    test_onboarding_navigation()
