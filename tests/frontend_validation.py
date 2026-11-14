"""Additional Phase 1 edge cases and navigation audit; requires a running server."""
import os
import unittest
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('CONNECTLY_URL', 'http://127.0.0.1:3000')
ROOT = Path(__file__).resolve().parents[1]


class FrontendValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = sync_playwright().start()
        cls.browser = cls.runner.chromium.launch(
            executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'),
            args=['--no-sandbox'],
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runner.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width':1440,'height':900}, reduced_motion='reduce')
        self.page = self.context.new_page()
        self.page.set_default_timeout(5000)
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('console', lambda msg: self.errors.append(msg.text) if msg.type=='error' else None)
        self.page.goto(BASE, wait_until='networkidle')

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def test_emoji_respects_limit_and_selection(self):
        text = self.page.locator('#post-text')
        for length in [997,998,999,1000]:
            with self.subTest(length=length):
                text.fill('a'*length)
                self.page.locator('#emoji-button').click()
                self.assertLessEqual(text.evaluate('(e)=>e.value.length'),1000)
        text.evaluate('(e)=>e.setSelectionRange(995,1000)')
        self.page.locator('#emoji-button').click()
        self.assertEqual(text.input_value(),'a'*995+' 😊')

    def test_notifications_dismiss_on_every_outside_action(self):
        page = self.page
        for target in ['[data-view="saved"]','[data-view="explore"]','[data-view="home"]','#post-text','#quiet-moments [data-action="like"]','#new-post']:
            with self.subTest(target=target):
                page.locator('#notifications-button').click()
                expect(page.locator('#notifications')).to_be_visible()
                page.locator(target).click()
                expect(page.locator('#notifications')).to_be_hidden()
                expect(page.locator('#notifications-button')).to_have_attribute('aria-expanded','false')
        page.locator('#notifications-button').click()
        page.locator('#notifications h2').click()
        expect(page.locator('#notifications')).to_be_visible()

    def test_compact_navigation_has_accessible_names(self):
        page = self.page
        page.set_viewport_size({'width':700,'height':900})
        for name, view in [('Home','home'),('Explore','explore'),('Bookmarks','saved')]:
            page.get_by_role('button',name=name,exact=True).click()
            expect(page.locator(f'[data-view="{view}"]')).to_have_attribute('aria-current','page')
        page.get_by_role('button',name='My profile',exact=True).click()
        expect(page.locator('#profile-dialog')).to_be_visible()
        page.keyboard.press('Escape')
        page.get_by_role('button',name='Create a post',exact=True).click()
        expect(page.locator('#post-text')).to_be_focused()

    def test_dialog_accessible_titles_and_all_close_routes(self):
        page = self.page
        page.locator('#quiet-moments [data-profile]').click()
        expect(page.get_by_role('dialog',name='Maya Bennett',exact=True)).to_be_visible()
        page.get_by_role('button',name='Close profile',exact=True).click()
        page.locator('.header-actions [data-profile]').click()
        expect(page.get_by_role('dialog',name='Alex Morgan',exact=True)).to_be_visible()
        page.mouse.click(2,2)
        expect(page.locator('#profile-dialog')).to_be_hidden()
        page.locator('[data-about]').click()
        expect(page.get_by_role('dialog',name='Welcome to Connectly.',exact=True)).to_be_visible()
        page.get_by_role('button',name='Close about dialog',exact=True).click()
        page.locator('#about-button').click()
        page.locator('.dialog-done').click()
        expect(page.locator('#about-dialog')).to_be_hidden()

    def test_all_topics_suggestions_and_discovery_cta(self):
        page = self.page
        page.locator('#toggle-suggestions').click()
        for button in page.locator('.suggestion-user').all():
            button.click()
            expect(page.locator('#profile-dialog')).to_be_visible()
            page.keyboard.press('Escape')
        for topic in ['DesignInspiration','SlowLiving','BuildInPublic','WeekendAdventures']:
            page.locator(f'[data-topic="{topic}"]').click()
            self.assertGreater(page.locator('.post-card').count(),0)
            expect(page.locator('.post-copy').first).to_contain_text('#'+topic)
        page.locator('[data-explore]').click()
        expect(page.locator('.post-card')).to_have_count(4)
        expect(page.locator('#active-query')).to_be_hidden()

    def test_links_resources_unique_ids_and_permalink(self):
        page = self.page
        # Rendered links, including local CSS/icon resources and fragment targets.
        for href in page.locator('a[href],link[href]').evaluate_all('(els)=>els.map(e=>e.getAttribute("href"))'):
            if href.startswith('#'):
                self.assertEqual(page.locator('[id="'+href[1:]+'"]').count(),1,href)
            else:
                response=page.request.get(urljoin(BASE+'/',href))
                self.assertEqual(response.status,200,href)
        ids=page.locator('[id]').evaluate_all('(els)=>els.map(e=>e.id)')
        self.assertEqual(len(ids),len(set(ids)))
        page.goto(BASE+'/#keep-exploring',wait_until='networkidle')
        bounds=page.locator('#keep-exploring').bounding_box()
        self.assertGreaterEqual(bounds['y'],page.locator('.topbar').bounding_box()['height'])
        self.assertLess(bounds['y'],900)
        page.locator('[data-view="saved"]').click()
        page.locator('.brand').click()
        expect(page.locator('[data-view="home"]')).to_have_attribute('aria-current','page')
        expect(page.locator('.post-card')).to_have_count(4)

    def test_every_local_photo_file_decodes(self):
        for path in (ROOT/'public/assets').rglob('*'):
            if path.suffix.lower() in ['.jpg','.png','.svg','.webp']:
                relative=path.relative_to(ROOT/'public').as_posix()
                result=self.page.evaluate('''async src=>{const image=new Image();image.src=src;await image.decode();return image.naturalWidth>0}''',relative)
                self.assertTrue(result,relative)

    def test_clipboard_denied_fallback(self):
        page = self.page
        page.evaluate("() => { navigator.clipboard.writeText=()=>Promise.reject(new Error('Clipboard unavailable')); }")
        copied=[]
        def on_dialog(dialog):
            copied.append(dialog.default_value)
            dialog.dismiss()
        page.on('dialog',on_dialog)
        page.locator('#quiet-moments [data-action="share"]').click()
        self.assertEqual(len(copied),1)
        self.assertTrue(copied[0].endswith('#quiet-moments'))

    def test_attachment_rejections_and_recovery(self):
        page = self.page
        upload=page.locator('#post-photo')
        upload.set_input_files({'name':'large.jpg','mimeType':'image/jpeg','buffer':b'x'*(5*1024*1024+1)})
        expect(page.locator('#composer-error')).to_contain_text('under 5 MB')
        expect(page.locator('#publish-post')).to_be_disabled()
        upload.set_input_files({'name':'broken.jpg','mimeType':'image/jpeg','buffer':b'not actually an image'})
        expect(page.locator('#composer-error')).to_contain_text('could not be read')
        expect(page.locator('#attachment-preview')).to_be_hidden()
        expect(page.locator('#publish-post')).to_be_disabled()
        upload.set_input_files(str(ROOT/'public/assets/images/mountains.jpg'))
        page.wait_for_function('document.querySelector("#attachment-image").naturalWidth > 0')
        expect(page.locator('#attachment-preview')).to_be_visible()
        expect(page.locator('#composer-error')).to_be_hidden()

    def test_blank_and_maximum_comments(self):
        page=self.page
        page.locator('#small-progress [data-action="comments"]').click()
        form=page.locator('#small-progress .comment-form')
        form.locator('input').fill('   ')
        form.locator('button').click()
        expect(page.locator('#small-progress .comment')).to_have_count(0)
        form.locator('input').fill('x'*500)
        form.locator('button').click()
        expect(page.locator('#small-progress .comment p')).to_have_text('x'*500)
        page.set_viewport_size({'width':320,'height':640})
        self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))

    def test_all_profiles_follow_state_stays_in_sync(self):
        page=self.page
        page.locator('#discovery [data-follow="daniel"]').click()
        page.locator('#small-progress [data-profile]').click()
        follow=page.locator('#profile-dialog [data-follow="daniel"]')
        expect(follow).to_have_attribute('aria-pressed','true')
        follow.click()
        expect(page.locator('#discovery [data-follow="daniel"]')).to_have_attribute('aria-pressed','false')

    def test_normal_motion_breakpoints_and_back_to_top(self):
        page=self.page
        page.emulate_media(reduced_motion='no-preference')
        self.assertEqual(page.evaluate('getComputedStyle(document.documentElement).scrollBehavior'),'smooth')
        for width,height in [(375,667),(667,375),(641,800),(760,900),(761,900),(1023,768),(1024,768),(1920,1080)]:
            with self.subTest(viewport=(width,height)):
                page.set_viewport_size({'width':width,'height':height})
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        page.locator('#back-to-top').click()
        page.wait_for_function('window.scrollY===0')

    def test_mobile_touch_interactions_and_landscape(self):
        self.context.close()
        self.context=self.browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=2,reduced_motion='reduce')
        self.page=self.context.new_page()
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('console', lambda msg: self.errors.append(msg.text) if msg.type=='error' else None)
        page=self.page
        page.goto(BASE,wait_until='networkidle')
        page.locator('#quiet-moments [data-action="like"]').tap()
        expect(page.locator('#quiet-moments .like-count')).to_have_text('129 likes')
        page.locator('#quiet-moments [data-action="comments"]').tap()
        page.locator('#quiet-moments .comment-form input').fill('A little connection from my phone.')
        page.locator('#quiet-moments .comment-form button').tap()
        expect(page.locator('#quiet-moments .comment').last.locator('p')).to_have_text('A little connection from my phone.')
        page.locator('#quiet-moments [data-action="bookmark"]').tap()
        page.locator('[data-view="saved"]').tap()
        expect(page.locator('.post-card')).to_have_count(1)
        page.locator('#quiet-moments [data-action="bookmark"]').tap()
        expect(page.locator('.empty-state')).to_be_visible()
        page.locator('[data-view="home"]').tap()
        page.locator('.main-nav [data-profile]').tap()
        expect(page.get_by_role('dialog',name='Alex Morgan')).to_be_visible()
        page.locator('#profile-dialog .dialog-close').tap()
        page.set_viewport_size({'width':844,'height':390})
        self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        page.locator('[data-view="explore"]').tap()
        expect(page.locator('[data-view="explore"]')).to_have_attribute('aria-current','page')


if __name__=='__main__':
    unittest.main(verbosity=2)
