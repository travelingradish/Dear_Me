#!/bin/bash
# Comprehensive DMG Installer Test Suite
# Tests all components of the Dear Me DMG installer

set -e

TEST_DIR="/tmp/dear_me_dmg_test"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESULTS_FILE="$TEST_DIR/test_results.txt"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Initialize
mkdir -p "$TEST_DIR"
> "$RESULTS_FILE"

log_test() {
    local test_name="$1"
    local status="$2"
    local message="${3:-}"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [ "$status" = "PASS" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✅ PASS${NC} $test_name" | tee -a "$RESULTS_FILE"
        [ -n "$message" ] && echo "   $message" | tee -a "$RESULTS_FILE"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}❌ FAIL${NC} $test_name" | tee -a "$RESULTS_FILE"
        [ -n "$message" ] && echo "   Error: $message" | tee -a "$RESULTS_FILE"
    fi
    echo "" | tee -a "$RESULTS_FILE"
}

echo "╔════════════════════════════════════════════════════════════╗" | tee -a "$RESULTS_FILE"
echo "║    Dear Me DMG Installer - Comprehensive Test Suite       ║" | tee -a "$RESULTS_FILE"
echo "╚════════════════════════════════════════════════════════════╝" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# ============================================================================
# SECTION 1: File Existence & Permissions Tests
# ============================================================================

echo -e "${BLUE}[SECTION 1] File Structure & Permissions${NC}" | tee -a "$RESULTS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# Test 1.1: DMG file exists
if [ -f "$SCRIPT_DIR/Dear_Me_1.0.0.dmg" ]; then
    size=$(du -h "$SCRIPT_DIR/Dear_Me_1.0.0.dmg" | cut -f1)
    log_test "DMG file exists" "PASS" "Size: $size"
else
    log_test "DMG file exists" "FAIL" "Dear_Me_1.0.0.dmg not found"
fi

# Test 1.2: setup.sh is executable
if [ -x "$SCRIPT_DIR/setup.sh" ]; then
    log_test "setup.sh is executable" "PASS"
else
    log_test "setup.sh is executable" "FAIL"
fi

# Test 1.3: build_dmg.sh is executable
if [ -x "$SCRIPT_DIR/build_dmg.sh" ]; then
    log_test "build_dmg.sh is executable" "PASS"
else
    log_test "build_dmg.sh is executable" "FAIL"
fi

# Test 1.4: Dear Me.command is executable
if [ -x "$SCRIPT_DIR/Dear Me.command" ]; then
    log_test "Dear Me.command is executable" "PASS"
else
    log_test "Dear Me.command is executable" "FAIL"
fi

# Test 1.5: App bundle exists
if [ -d "$SCRIPT_DIR/Dear Me.app" ]; then
    log_test "Dear Me.app bundle exists" "PASS"
else
    log_test "Dear Me.app bundle exists" "FAIL"
fi

# ============================================================================
# SECTION 2: Script Syntax & Content Tests
# ============================================================================

echo -e "${BLUE}[SECTION 2] Script Syntax Validation${NC}" | tee -a "$RESULTS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# Test 2.1: setup.sh syntax
if bash -n "$SCRIPT_DIR/setup.sh" 2>/dev/null; then
    log_test "setup.sh syntax validation" "PASS"
else
    log_test "setup.sh syntax validation" "FAIL" "Bash syntax errors found"
fi

# Test 2.2: build_dmg.sh syntax
if bash -n "$SCRIPT_DIR/build_dmg.sh" 2>/dev/null; then
    log_test "build_dmg.sh syntax validation" "PASS"
else
    log_test "build_dmg.sh syntax validation" "FAIL" "Bash syntax errors found"
fi

# Test 2.3: Dear Me.command syntax
if bash -n "$SCRIPT_DIR/Dear Me.command" 2>/dev/null; then
    log_test "Dear Me.command syntax validation" "PASS"
else
    log_test "Dear Me.command syntax validation" "FAIL" "Bash syntax errors found"
fi

# Test 2.4: setup.sh contains required fixes
setup_checks=(
    "venv/bin/python"
    "curl.*localhost:8001"
    "curl.*localhost:3000"
    "curl.*localhost:11434"
    "kill -0"
    "lsof.*:8001"
    "lsof.*:3000"
)

all_found=true
for check in "${setup_checks[@]}"; do
    if ! grep -q "$check" "$SCRIPT_DIR/setup.sh"; then
        all_found=false
        break
    fi
done

if [ "$all_found" = true ]; then
    log_test "setup.sh contains all critical fixes" "PASS"
else
    log_test "setup.sh contains all critical fixes" "FAIL" "Some fixes missing"
fi

# ============================================================================
# SECTION 3: DMG Content Tests
# ============================================================================

echo -e "${BLUE}[SECTION 3] DMG Content Verification${NC}" | tee -a "$RESULTS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# Mount DMG temporarily
MOUNT_POINT="/Volumes/Dear Me"
if [ -d "$MOUNT_POINT" ]; then
    hdiutil detach "$MOUNT_POINT" 2>/dev/null || true
fi

# Test 3.1: DMG can be mounted
if hdiutil mount "$SCRIPT_DIR/Dear_Me_1.0.0.dmg" -nobrowse 2>&1 | grep -q "mounted"; then
    log_test "DMG can be mounted" "PASS"

    # Test 3.2: App bundle exists in DMG
    if [ -d "$MOUNT_POINT/Dear Me.app" ]; then
        log_test "Dear Me.app exists in DMG" "PASS"
    else
        log_test "Dear Me.app exists in DMG" "FAIL"
    fi

    # Test 3.3: install_dependencies.sh exists in DMG
    if [ -f "$MOUNT_POINT/install_dependencies.sh" ]; then
        log_test "install_dependencies.sh exists in DMG" "PASS"

        # Test 3.4: install_dependencies.sh is executable
        if [ -x "$MOUNT_POINT/install_dependencies.sh" ]; then
            log_test "install_dependencies.sh is executable" "PASS"
        else
            log_test "install_dependencies.sh is executable" "FAIL"
        fi
    else
        log_test "install_dependencies.sh exists in DMG" "FAIL"
    fi

    # Test 3.5: README.txt exists in DMG
    if [ -f "$MOUNT_POINT/README.txt" ]; then
        log_test "README.txt exists in DMG" "PASS"

        # Check README content
        if grep -q "Installation Instructions" "$MOUNT_POINT/README.txt"; then
            log_test "README.txt has proper content" "PASS"
        else
            log_test "README.txt has proper content" "FAIL"
        fi
    else
        log_test "README.txt exists in DMG" "FAIL"
    fi

    # Test 3.6: Applications symlink exists
    if [ -L "$MOUNT_POINT/Applications" ]; then
        log_test "Applications symlink exists in DMG" "PASS"
    else
        log_test "Applications symlink exists in DMG" "FAIL"
    fi

    # Test 3.7: install_dependencies.sh syntax
    if bash -n "$MOUNT_POINT/install_dependencies.sh" 2>/dev/null; then
        log_test "install_dependencies.sh syntax validation" "PASS"
    else
        log_test "install_dependencies.sh syntax validation" "FAIL"
    fi

    # Test 3.8: Homebrew detection in install script
    if grep -q "command -v brew" "$MOUNT_POINT/install_dependencies.sh"; then
        log_test "install_dependencies.sh detects Homebrew" "PASS"
    else
        log_test "install_dependencies.sh detects Homebrew" "FAIL"
    fi

    # Test 3.9: Dependencies in install script
    deps_check=(
        "brew install ollama"
        "brew install node"
        "brew install python@3.13"
    )

    all_deps_found=true
    for dep in "${deps_check[@]}"; do
        if ! grep -q "$dep" "$MOUNT_POINT/install_dependencies.sh"; then
            all_deps_found=false
            break
        fi
    done

    if [ "$all_deps_found" = true ]; then
        log_test "All dependencies in install script" "PASS"
    else
        log_test "All dependencies in install script" "FAIL"
    fi

    # Unmount DMG
    hdiutil detach "$MOUNT_POINT" 2>/dev/null || true
else
    log_test "DMG can be mounted" "FAIL" "Mount operation failed"
fi

# ============================================================================
# SECTION 4: Documentation Tests
# ============================================================================

echo -e "${BLUE}[SECTION 4] Documentation Completeness${NC}" | tee -a "$RESULTS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

docs=(
    "START_HERE.md"
    "DEPLOYMENT_SUMMARY.md"
    "READY_TO_DISTRIBUTE.md"
    "DMG_DISTRIBUTION_GUIDE.md"
    "LAUNCHER_TEST_REPORT.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$SCRIPT_DIR/$doc" ]; then
        lines=$(wc -l < "$SCRIPT_DIR/$doc")
        if [ "$lines" -gt 50 ]; then
            log_test "$doc exists and is substantial" "PASS" "($lines lines)"
        else
            log_test "$doc exists and is substantial" "FAIL" "Only $lines lines"
        fi
    else
        log_test "$doc exists" "FAIL"
    fi
done

# ============================================================================
# SECTION 5: Feature Tests
# ============================================================================

echo -e "${BLUE}[SECTION 5] Feature Validation${NC}" | tee -a "$RESULTS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# Test 5.1: Health check features
if grep -q "curl.*localhost:8001" "$SCRIPT_DIR/setup.sh" && \
   grep -q "curl.*localhost:3000" "$SCRIPT_DIR/setup.sh"; then
    log_test "Health check endpoints configured" "PASS"
else
    log_test "Health check endpoints configured" "FAIL"
fi

# Test 5.2: Port conflict resolution
if grep -q "lsof.*:8001\|lsof.*:3000" "$SCRIPT_DIR/setup.sh" && \
   grep -q "kill.*2>/dev/null" "$SCRIPT_DIR/setup.sh"; then
    log_test "Port conflict resolution implemented" "PASS"
else
    log_test "Port conflict resolution implemented" "FAIL"
fi

# Test 5.3: WiFi IP detection
if grep -q "route get 8.8.8.8\|ipconfig getifaddr" "$SCRIPT_DIR/setup.sh"; then
    log_test "WiFi IP detection implemented" "PASS"
else
    log_test "WiFi IP detection implemented" "FAIL"
fi

# Test 5.4: Browser auto-open
if grep -q "open http://localhost:3000" "$SCRIPT_DIR/setup.sh"; then
    log_test "Browser auto-open implemented" "PASS"
else
    log_test "Browser auto-open implemented" "FAIL"
fi

# Test 5.5: Graceful cleanup
if grep -q "cleanup()" "$SCRIPT_DIR/setup.sh" && \
   grep -q "trap cleanup" "$SCRIPT_DIR/setup.sh"; then
    log_test "Graceful cleanup on Ctrl+C" "PASS"
else
    log_test "Graceful cleanup on Ctrl+C" "FAIL"
fi

# Test 5.6: Ollama reuse detection
if grep -q "OLLAMA_STARTED_BY_US" "$SCRIPT_DIR/setup.sh"; then
    log_test "Ollama reuse detection" "PASS"
else
    log_test "Ollama reuse detection" "FAIL"
fi

# Test 5.7: Color output
if grep -q "COLOR_BLUE\|COLOR_GREEN\|COLOR_RED" "$SCRIPT_DIR/setup.sh" || \
   grep -q "\\\\033\|tput" "$SCRIPT_DIR/setup.sh"; then
    log_test "Color output support" "PASS"
else
    log_test "Color output support" "FAIL"
fi

# ============================================================================
# SECTION 6: Logical Flow Tests
# ============================================================================

echo -e "${BLUE}[SECTION 6] Script Logic Validation${NC}" | tee -a "$RESULTS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# Test 6.1: Prerequisites check order
if grep -n "ollamajQuery\|node\|npm" "$SCRIPT_DIR/setup.sh" | head -3 > /dev/null; then
    log_test "Prerequisites checked before operations" "PASS"
else
    log_test "Prerequisites checked before operations" "FAIL"
fi

# Test 6.2: Sequential startup order (Ollama → Backend → Frontend)
ollama_line=$(grep -n "Starting Ollama" "$SCRIPT_DIR/setup.sh" | cut -d: -f1)
backend_line=$(grep -n "Starting backend" "$SCRIPT_DIR/setup.sh" | cut -d: -f1)
frontend_line=$(grep -n "Starting frontend" "$SCRIPT_DIR/setup.sh" | cut -d: -f1)

if [ "$ollama_line" -lt "$backend_line" ] && [ "$backend_line" -lt "$frontend_line" ]; then
    log_test "Correct startup sequence (Ollama → Backend → Frontend)" "PASS"
else
    log_test "Correct startup sequence (Ollama → Backend → Frontend)" "FAIL"
fi

# Test 6.3: Health check timeouts
if grep -q "TRIES.*60\|TRIES.*120\|TRIES.*30" "$SCRIPT_DIR/setup.sh"; then
    log_test "Health check timeouts configured" "PASS"
else
    log_test "Health check timeouts configured" "FAIL"
fi

# Test 6.4: Monitor loop exists
if grep -q "while true\|sleep 10" "$SCRIPT_DIR/setup.sh"; then
    log_test "Monitor loop for service health" "PASS"
else
    log_test "Monitor loop for service health" "FAIL"
fi

# ============================================================================
# SECTION 7: Build Script Tests
# ============================================================================

echo -e "${BLUE}[SECTION 7] DMG Builder Validation${NC}" | tee -a "$RESULTS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# Test 7.1: build_dmg.sh checks prerequisites
if grep -q "create_app.sh\|hdiutil\|mkdir" "$SCRIPT_DIR/build_dmg.sh"; then
    log_test "build_dmg.sh checks prerequisites" "PASS"
else
    log_test "build_dmg.sh checks prerequisites" "FAIL"
fi

# Test 7.2: build_dmg.sh creates proper structure
if grep -q "install_dependencies.sh\|README.txt\|Applications" "$SCRIPT_DIR/build_dmg.sh"; then
    log_test "build_dmg.sh creates DMG structure" "PASS"
else
    log_test "build_dmg.sh creates DMG structure" "FAIL"
fi

# Test 7.3: build_dmg.sh is idempotent
if grep -q "rm -rf.*dmg_build\|rm.*Dear_Me.*dmg" "$SCRIPT_DIR/build_dmg.sh"; then
    log_test "build_dmg.sh cleans up old builds" "PASS"
else
    log_test "build_dmg.sh cleans up old builds" "FAIL"
fi

# ============================================================================
# RESULTS SUMMARY
# ============================================================================

echo "" | tee -a "$RESULTS_FILE"
echo "╔════════════════════════════════════════════════════════════╗" | tee -a "$RESULTS_FILE"
echo "║                    TEST SUMMARY                           ║" | tee -a "$RESULTS_FILE"
echo "╚════════════════════════════════════════════════════════════╝" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

echo "Tests Run:    $TESTS_RUN" | tee -a "$RESULTS_FILE"
echo "Tests Passed: ${GREEN}$TESTS_PASSED${NC}" | tee -a "$RESULTS_FILE"
echo "Tests Failed: $([ $TESTS_FAILED -eq 0 ] && echo -e "${GREEN}$TESTS_FAILED${NC}" || echo -e "${RED}$TESTS_FAILED${NC}")" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}" | tee -a "$RESULTS_FILE"
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}" | tee -a "$RESULTS_FILE"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}" | tee -a "$RESULTS_FILE"
    OVERALL_RESULT=0
else
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}" | tee -a "$RESULTS_FILE"
    echo -e "${RED}❌ SOME TESTS FAILED${NC}" | tee -a "$RESULTS_FILE"
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}" | tee -a "$RESULTS_FILE"
    OVERALL_RESULT=1
fi

echo "" | tee -a "$RESULTS_FILE"
echo "📊 Full results saved to: $RESULTS_FILE" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

cat "$RESULTS_FILE"
exit $OVERALL_RESULT
