from pathlib import Path


async def check_if_click_successful(page, selector, url_pattern, logger):
    """
    Verifies if a click operation was successful by checking:
    1. Network idle state
    2. URL navigation pattern match
    3. Element state changes

    Returns:
        bool: True if any success indicator is detected, False otherwise
    """
    success = False
    original_url = page.url

    # 1. Check network idle state
    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
        logger.info(f"Network idle check completed for {selector}")
        success = True
    except TimeoutError:
        logger.warning(f"Network did not reach idle state for {selector}")

    # 2. Check URL navigation pattern
    try:
        await page.wait_for_url(
            url_pattern,
            timeout=5000,
            wait_until="domcontentloaded"
        )
        logger.info(f"URL pattern match successful: {url_pattern}")
        return True  # Return immediately on URL match
    except TimeoutError:
        logger.warning(f"URL did not change to match pattern: {url_pattern}")

    # 3. Verify element state changes (if URL didn't change)
    if not success:
        try:
            # Check if element disappeared or changed state
            if not await page.is_visible(selector):
                logger.info(f"Element vanished after click: {selector}")
                success = True
            else:
                # Check for visual/state changes
                is_now_disabled = await page.evaluate(f"""() => {{
                    const el = document.querySelector('{selector}');
                    return el && (el.disabled || el.getAttribute('aria-disabled') === 'true');
                }}""")

                if is_now_disabled:
                    logger.info(f"Element state changed to disabled: {selector}")
                    success = True

                # Check for CSS change indicating success
                has_success_style = await page.evaluate(f"""() => {{
                    const el = document.querySelector('{selector}');
                    if (!el) return false;
                    const style = getComputedStyle(el);
                    return style.backgroundColor.includes('green') || 
                           style.border.includes('green') ||
                           style.color.includes('green');
                }}""")

                if has_success_style:
                    logger.info(f"Visual success indicators detected: {selector}")
                    success = True
        except Exception as e:
            logger.error(f"Element state check failed: {str(e)}")

    # 4. Final fallback: Check if URL changed at all
    if not success:
        current_url = page.url
        if current_url != original_url:
            logger.info(f"URL changed from {original_url} to {current_url}")
            success = True

    return success


async def check_if_its_visible(page, selector, logger):
    """
    Checks if a selector is visible using multiple methods.
    Returns True as soon as one method confirms visibility.
    :param page: Playwright page context
    :param selector: Element selector
    :return: Boolean
    """
    # Method 1: Using is_visible()
    try:
        if await page.locator(selector).is_visible():
            logger.info(f"is_visible() confirmed visibility for: {selector}")
            return True
    except Exception as e:
        logger.error(f"is_visible() failed for {selector}: {str(e)}")

    # Method 2: CSS visibility check
    try:
        visible = await page.locator(selector).evaluate("""
            el => {
                const style = window.getComputedStyle(el);
                return style.visibility !== 'hidden' && 
                       style.display !== 'none' &&
                       el.offsetWidth > 0 &&
                       el.offsetHeight > 0;
            }
        """)
        if visible:
            logger.info(f"CSS check confirmed visibility for: {selector}")
            return True
    except Exception as e:
        logger.error(f"CSS visibility check failed for {selector}: {str(e)}")

    # Method 3: Bounding box check
    try:
        bounding_box = await page.locator(selector).bounding_box()
        if bounding_box and bounding_box['width'] > 0 and bounding_box['height'] > 0:
            logger.info(f"Bounding box confirmed visibility for: {selector}")
            return True
    except Exception as e:
        logger.error(f"Bounding box check failed for {selector}: {str(e)}")

    # Method 4: Wait-based verification
    try:
        await page.wait_for_selector(selector, state="visible", timeout=3000)
        logger.info(f"Wait-based verification succeeded for: {selector}")
        return True
    except Exception as e:
        logger.error(f"Wait-based verification failed for {selector}: {str(e)}")

    # Method 5: Element handle check
    try:
        handle = await page.locator(selector).element_handle()
        if handle:
            logger.info(f"Element handle confirmed existence for: {selector}")
            return True
    except Exception as e:
        logger.error(f"Element handle check failed for {selector}: {str(e)}")

    logger.warning(f"All visibility checks failed for: {selector}")
    return False


def parse_count(text: str):
    """Convert strings like '411K', '2,876', '1.2M' to int where possible."""
    if not text:
        return None
    s = text.strip()
    # remove non-breaking spaces
    s = s.replace('\xa0', '').replace('\u202f', '')
    # direct digits with commas
    if re.match(r'^[\d,\.]+$', s):
        try:
            # handle decimals by removing fractional part for counts
            return int(float(s.replace(',', '')))
        except Exception:
            return None
    m = re.match(r'^([\d,.]*\d)([kKmM])$', s)
    if m:
        num = float(m.group(1).replace(',', ''))
        suffix = m.group(2).lower()
        if suffix == 'k':
            return int(num * 1000)
        if suffix == 'm':
            return int(num * 1000000)
    # fallback: find first number-like token
    m2 = re.search(r'([\d,\.]+)', s)
    if m2:
        try:
            return int(float(m2.group(1).replace(',', '')))
        except Exception:
            return None
    return None