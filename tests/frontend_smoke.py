"""End-to-end checks against a running Connectly static server.

Uses the environment's existing Python Playwright + Chromium; no app dependencies.
"""
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('CONNECTLY_URL', 'http://127.0.0.1:3000')
OUTPUT = Path(os.environ.get('CONNECTLY_TEST_OUTPUT', 'test-results'))
OUTPUT.mkdir(parents=True, exist_ok=True)
(OUTPUT/'results.json').unlink(missing_ok=True)
ROOT = Path(__file__).resolve().parents[1]
passed = []


def check(name):
    passed.append(name)
    print(f'PASS {name}', flush=True)


with sync_playwright() as runner:
    browser = runner.chromium.launch(
        executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'),
        headless=True,
        args=['--no-sandbox'],
    )
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
    context.grant_permissions(['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    errors, failed_requests, external_requests = [], [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
    page.on('requestfailed', lambda request: failed_requests.append(request.url))
    page.on('response', lambda response: failed_requests.append(f'{response.status}: {response.url}') if response.status >= 400 else None)
    page.on('request', lambda request: external_requests.append(request.url) if request.url.startswith('http') and not request.url.startswith(BASE) else None)

    response = page.goto(BASE, wait_until='networkidle')
    assert response.status == 200
    expect(page).to_have_title('Connectly — Your daily connection')
    expect(page.locator('.post-card')).to_have_count(4)
    expect(page.locator('.right-sidebar')).to_be_visible()
    check('Homepage loads with four posts and three desktop columns')

    first = page.locator('#quiet-moments')
    like = first.locator('[data-action="like"]')
    like.click()
    expect(like).to_have_attribute('aria-pressed', 'true')
    expect(first.locator('.like-count')).to_have_text('129 likes')
    like.click()
    expect(first.locator('.like-count')).to_have_text('128 likes')
    like.click()
    check('Likes toggle and update totals')

    first.locator('[data-action="bookmark"]').click()
    page.locator('[data-view="saved"]').click()
    expect(page.locator('.post-card')).to_have_count(1)
    expect(page.locator('#quiet-moments')).to_be_visible()
    page.locator('#quiet-moments [data-action="bookmark"]').click()
    expect(page.locator('.empty-state')).to_be_visible()
    page.locator('[data-view="home"]').click()
    page.locator('#quiet-moments [data-action="bookmark"]').click()
    check('Bookmarks view, removal, count, and empty state')

    first.locator('[data-action="comments"]').click()
    expect(first.locator('.comments-panel')).to_be_visible()
    expect(first.locator('.comment')).to_have_count(2)
    sample = '<img src=x onerror="window.injected=true"> Love this perspective!'
    first.locator('.comment-form input').fill(sample)
    first.locator('.comment-form button').click()
    expect(first.locator('.comment')).to_have_count(3)
    expect(first.locator('.comment').last.locator('p')).to_have_text(sample)
    expect(first.locator('.comment-count')).to_have_text('3 comments')
    assert page.evaluate('window.injected') is None
    first.locator('[data-action="comments"]').click()
    expect(first.locator('.comments-panel')).to_be_hidden()
    check('Comments expand, accept literal text safely, update counts, and collapse')

    follow = page.locator('#discovery [data-follow="daniel"]')
    follow.click()
    expect(follow).to_have_attribute('aria-pressed', 'true')
    page.locator('[data-filter="following"]').click()
    expect(page.locator('.post-card')).to_have_count(2)
    expect(page.locator('#small-progress')).to_be_visible()
    follow.click()
    expect(page.locator('.post-card')).to_have_count(1)
    follow.click()
    page.locator('[data-filter="for-you"]').click()
    check('Follow toggles update the Following feed immediately')

    page.locator('#toggle-suggestions').click()
    expect(page.locator('.suggestion')).to_have_count(5)
    page.locator('#toggle-suggestions').click()
    expect(page.locator('.suggestion')).to_have_count(3)
    page.locator('[data-topic="DesignInspiration"]').click()
    expect(page.locator('.post-card')).to_have_count(1)
    expect(page.locator('#creative-space')).to_be_visible()
    page.locator('#clear-query').click()
    expect(page.locator('.post-card')).to_have_count(4)
    page.locator('#search-input').fill('james')
    expect(page.locator('.post-card')).to_have_count(1)
    page.locator('#search-input').fill('no matching topic at all')
    expect(page.locator('.empty-state')).to_be_visible()
    page.locator('#search-input').fill('')
    page.locator('[data-view="home"]').click()
    page.locator('#sort-button').click()
    expect(page.locator('.post-card').first).to_have_attribute('id', 'keep-exploring')
    check('Suggestions, trends, search, empty results, and popular sorting')

    page.locator('.post-card').first.locator('[data-profile]').click()
    expect(page.locator('#profile-dialog')).to_be_visible()
    expect(page.locator('#profile-content h2')).to_have_text('James Wilson')
    page.keyboard.press('Escape')
    expect(page.locator('#profile-dialog')).to_be_hidden()
    page.locator('#notifications-button').click()
    expect(page.locator('#notifications')).to_be_visible()
    page.keyboard.press('Escape')
    expect(page.locator('#notifications')).to_be_hidden()
    page.locator('#about-button').click()
    expect(page.locator('#about-dialog')).to_be_visible()
    page.locator('.dialog-done').click()
    page.keyboard.press('/')
    expect(page.locator('#search-input')).to_be_focused()
    check('Profiles, notifications, about dialog, Escape, and search shortcut')

    page.locator('[data-view="home"]').click()
    page.locator('#quiet-moments [data-action="share"]').click()
    assert page.evaluate('navigator.clipboard.readText()').endswith('#quiet-moments')
    check('Share copies the seeded post permalink')

    expect(page.locator('#publish-post')).to_be_disabled()
    page.locator('#post-text').fill('   ')
    expect(page.locator('#publish-post')).to_be_disabled()
    page.locator('#post-text').fill('A little progress today. <script>window.injected=true</script>')
    page.locator('#emoji-button').click()
    expect(page.locator('#post-text')).to_have_value('A little progress today. <script>window.injected=true</script> 😊')
    page.locator('#publish-post').click()
    expect(page.locator('.post-card')).to_have_count(5)
    expect(page.locator('.post-card').first.locator('.post-copy')).to_contain_text('<script>window.injected=true</script>')
    assert page.evaluate('window.injected') is None
    expect(page.locator('#publish-post')).to_be_disabled()
    check('Composer validates empty input and publishes safe mock text and emoji')

    page.locator('#photo-button').focus()
    with page.expect_file_chooser() as picker:
        page.keyboard.press('Enter')
    picker.value.set_files([])
    check('Photo picker is usable from the keyboard')

    page.locator('#post-photo').set_input_files({'name':'invalid.txt','mimeType':'text/plain','buffer':b'not an image'})
    expect(page.locator('#composer-error')).to_be_visible()
    page.locator('#post-photo').set_input_files(str(ROOT/'public/assets/images/mountains.jpg'))
    expect(page.locator('#attachment-preview')).to_be_visible()
    page.wait_for_function('document.querySelector("#attachment-image").naturalWidth > 0')
    page.locator('#remove-photo').click()
    expect(page.locator('#attachment-preview')).to_be_hidden()
    expect(page.locator('#publish-post')).to_be_disabled()
    page.locator('#post-photo').set_input_files(str(ROOT/'public/assets/images/mountains.jpg'))
    page.locator('#publish-post').click()
    page.wait_for_function('document.querySelector(".post-card .post-media img").naturalWidth > 0')
    expect(page.locator('.post-card')).to_have_count(6)
    check('Local photo selection, validation, removal, and publishing')

    page.reload(wait_until='networkidle')
    expect(page.locator('.post-card')).to_have_count(4)
    expect(page.locator('#quiet-moments [data-action="like"]')).to_have_attribute('aria-pressed','true')
    expect(page.locator('#quiet-moments [data-action="bookmark"]')).to_have_attribute('aria-pressed','true')
    expect(page.locator('#discovery [data-follow="daniel"]')).to_have_attribute('aria-pressed','true')
    check('Preferences persist across reload; session posts reset as documented')

    # Decode every shipped image, including those lazy-loaded or inside closed panels.
    broken = page.locator('img[src]').evaluate_all('''async imgs => {
      const failures = await Promise.all(imgs.map(async i => {
        try { const probe = new Image(); probe.src = i.src; await probe.decode(); return null; }
        catch { return i.src; }
      })); return failures.filter(Boolean);
    }''')
    assert not broken, broken
    assert page.locator('[data-fallback]').count() == 0
    assert not external_requests, external_requests
    check('Every image decodes successfully with no runtime external requests or fallbacks')

    # Fresh initial UI in screenshots; also exercise navigation at each breakpoint.
    page.evaluate('localStorage.clear()')
    page.reload(wait_until='networkidle')
    for width in [320, 360, 390, 640, 700, 768, 1024, 1280, 1440]:
        page.set_viewport_size({'width':width,'height':900})
        page.evaluate('window.scrollTo(0,0)')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Horizontal overflow at {width}'
        expect(page.locator('.right-sidebar')).to_be_visible() if width>=1024 else expect(page.locator('.right-sidebar')).to_be_hidden()
        for selector in ['.topbar','.composer','.post-card','.left-sidebar']:
            box=page.locator(selector).first.bounding_box()
            assert box and box['width']>0 and box['x']>=0 and box['x']+box['width']<=width+1, (width,selector,box)
        page.locator('[data-view="saved"]').click()
        expect(page.locator('.empty-state')).to_be_visible()
        page.locator('[data-view="home"]').click()
        if width in [390,768,1440]:
            page.screenshot(path=str(OUTPUT/f'connectly-{width}.png'), full_page=True)
    check('Nine viewport widths: 320–1440px, working navigation, no horizontal overflow')

    page.set_viewport_size({'width':390,'height':844})
    page.locator('#quiet-moments [data-action="like"]').click()
    expect(page.locator('#quiet-moments .like-count')).to_have_text('129 likes')
    page.locator('#quiet-moments [data-profile]').click()
    page.locator('#profile-dialog [data-follow]').click()
    expect(page.locator('#profile-dialog [data-follow]')).to_have_attribute('aria-pressed','false')
    page.keyboard.press('Escape')
    page.locator('[data-filter="following"]').click()
    expect(page.locator('.empty-state')).to_be_visible()
    page.locator('[data-view="home"]').click()
    page.locator('#quiet-moments [data-action="comments"]').click()
    page.locator('#quiet-moments .comment-form input').fill('Love this on mobile!')
    page.locator('#quiet-moments .comment-form button').click()
    expect(page.locator('#quiet-moments .comment').last.locator('p')).to_have_text('Love this on mobile!')
    check('Mobile likes, profile follow toggle, empty Following feed, and comments')

    assert page.evaluate('getComputedStyle(document.documentElement).scrollBehavior') == 'auto'
    check('Reduced-motion preference disables smooth scrolling')
    assert not errors, errors
    assert not failed_requests, failed_requests
    check('No browser console errors, uncaught exceptions, or failed HTTP requests')
    context.close()

    # Damaged or blocked browser storage must not prevent the UI loading.
    for script in [
        "localStorage.setItem('connectly.preferences.v1','invalid json')",
        "Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage unavailable')}})",
    ]:
        isolated=browser.new_context()
        isolated.add_init_script(script)
        tab=isolated.new_page()
        tab.goto(BASE,wait_until='networkidle')
        expect(tab.locator('.post-card')).to_have_count(4)
        tab.locator('#quiet-moments [data-action="like"]').click()
        expect(tab.locator('#quiet-moments .like-count')).to_have_text('129 likes')
        isolated.close()
    check('App works with corrupt or unavailable localStorage')

    isolated = browser.new_context()
    tab = isolated.new_page()
    fragment_errors = []
    tab.on('pageerror', lambda error: fragment_errors.append(str(error)))
    tab.goto(BASE + '/#%invalid', wait_until='networkidle')
    expect(tab.locator('.post-card')).to_have_count(4)
    assert not fragment_errors, fragment_errors
    tab.keyboard.press('Tab')
    expect(tab.locator('.skip-link')).to_be_focused()
    tab.keyboard.press('Enter')
    expect(tab.locator('main')).to_be_focused()
    isolated.close()
    check('Malformed shared links are harmless and skip-to-feed works with keyboard')
    browser.close()

(OUTPUT/'results.json').write_text(json.dumps({'passed':len(passed),'checks':passed},indent=2)+'\n')
print(f'\n{len(passed)} checks passed. Screenshots and results: {OUTPUT.resolve()}')
