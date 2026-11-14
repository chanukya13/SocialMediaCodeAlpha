"""Image reliability and focused card-polish regressions for Phase 1.

Normal-load checks require zero failures; fault-injection tests deliberately
block or corrupt image responses to verify recovery without fallback loops.
"""
import os
import unittest
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get('CONNECTLY_URL', 'http://127.0.0.1:3000')


class FrontendImages(unittest.TestCase):
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
        self.context = self.browser.new_context(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
        self.page = self.context.new_page()
        self.page.set_default_timeout(5000)
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def load(self, path='/'):
        self.page.goto(BASE+path,wait_until='networkidle')
        expect(self.page.locator('.post-card')).to_have_count(4)

    def load_all_photos(self):
        self.page.locator('.avatar,.post-media img').evaluate_all('(imgs)=>imgs.forEach(i=>i.loading="eager")')
        self.page.wait_for_function('''() => [...document.querySelectorAll('.avatar,.post-media img')].every(i=>i.complete && i.naturalWidth>0)''')
        self.page.locator('.avatar,.post-media img').evaluate_all('async imgs=>{await Promise.all(imgs.map(i=>i.decode()))}')

    def test_normal_images_are_local_described_and_fully_loaded(self):
        console_errors, failures, external = [], [], []
        self.page.on('console',lambda msg:console_errors.append(msg.text) if msg.type=='error' else None)
        self.page.on('requestfailed',lambda request:failures.append(request.url))
        self.page.on('response',lambda response:failures.append(response.url) if response.status>=400 else None)
        self.page.on('request',lambda request:external.append(request.url) if request.url.startswith('http') and urlsplit(request.url).netloc!=urlsplit(BASE).netloc else None)
        self.load()
        self.page.locator('#toggle-suggestions').click()
        self.load_all_photos()
        for image in self.page.locator('.avatar,.post-media img').all():
            self.assertTrue(image.get_attribute('alt').strip())
            self.assertIsNone(image.get_attribute('data-fallback'))
            self.assertIn('/assets/images/',image.evaluate('(i)=>i.currentSrc'))
        self.assertEqual(console_errors,[])
        self.assertEqual(failures,[])
        self.assertEqual(external,[])

    def test_early_static_failures_are_recovered_after_module_load(self):
        self.page.route('**/assets/images/you.jpg',lambda route:route.abort())
        def delayed_main(route):
            response=route.fetch()
            route.fulfill(response=response,body='await new Promise(resolve=>setTimeout(resolve,800));\n'+response.text())
        self.page.route('**/js/main.js',delayed_main)
        self.page.add_init_script('''window.__earlyAvatarFailures=0;
          document.addEventListener('error',e=>{
            if(e.target instanceof HTMLImageElement && e.target.classList.contains('avatar') && !document.querySelector('.post-card')) window.__earlyAvatarFailures++;
          },true);''')
        self.load()
        self.assertGreaterEqual(self.page.evaluate('window.__earlyAvatarFailures'),3)
        avatars=self.page.locator('.header-actions .avatar,.sidebar-profile .avatar,.composer-top .avatar')
        expect(avatars).to_have_count(3)
        for image in avatars.all():
            expect(image).to_have_attribute('data-fallback','local')
            expect(image).to_have_attribute('src',BASE+'/assets/avatar-fallback.svg')
            self.assertIn('Alex Morgan',image.get_attribute('alt'))
            self.assertIn('unavailable',image.get_attribute('alt'))
        self.load_all_photos()

    def test_failed_photos_use_distinct_local_placeholders(self):
        self.page.route('**/assets/images/*.jpg',lambda route:route.abort())
        self.load()
        self.load_all_photos()
        for image in self.page.locator('.avatar').all():
            expect(image).to_have_attribute('data-fallback','local')
            expect(image).to_have_attribute('src',BASE+'/assets/avatar-fallback.svg')
        for image in self.page.locator('.post-media img').all():
            expect(image).to_have_attribute('data-fallback','local')
            expect(image).to_have_attribute('src',BASE+'/assets/image-fallback.svg')
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))

    def test_missing_placeholder_files_use_inline_images_without_retry_loops(self):
        self.page.route('**/assets/images/*.jpg',lambda route:route.abort())
        failed_fallbacks=[]
        def abort_fallback(route):
            failed_fallbacks.append(route.request.url)
            route.abort()
        self.page.route('**/assets/*fallback.svg',abort_fallback)
        self.load()
        self.load_all_photos()
        photos=self.page.locator('.avatar,.post-media img')
        for image in photos.all():
            expect(image).to_have_attribute('data-fallback','inline')
            self.assertTrue(image.get_attribute('src').startswith('data:image/svg+xml'))
        self.assertGreater(len(failed_fallbacks),0)
        self.assertLessEqual(len(failed_fallbacks),photos.count())
        self.page.locator('#quiet-moments [data-action="like"]').click()
        expect(self.page.locator('#quiet-moments .like-count')).to_have_text('129 likes')

    def test_corrupt_main_photo_keeps_card_and_meaningful_alt(self):
        self.page.route('**/assets/images/mountains.jpg',lambda route:route.fulfill(status=200,content_type='image/jpeg',body=b'not an image'))
        self.load()
        image=self.page.locator('#quiet-moments .post-media img')
        expect(image).to_have_attribute('data-fallback','local')
        self.load_all_photos()
        self.assertIn('forested mountains',image.get_attribute('alt'))
        self.assertIn('unavailable',image.get_attribute('alt'))
        self.page.locator('#quiet-moments [data-action="comments"]').click()
        expect(self.page.locator('#quiet-moments .comments-panel')).to_be_visible()

    def test_assets_and_fallbacks_work_under_a_subdirectory(self):
        def mount(route):
            path=urlsplit(route.request.url).path.removeprefix('/connectly')
            response=route.fetch(url=BASE+path)
            route.fulfill(response=response)
        self.page.route('**/connectly/**',mount)
        self.load('/connectly/index.html')
        self.load_all_photos()
        for image in self.page.locator('.avatar,.post-media img').all():
            self.assertIn('/connectly/assets/',image.evaluate('(i)=>i.currentSrc'))
        self.page.route('**/connectly/assets/images/mountains.jpg',lambda route:route.abort())
        self.page.reload(wait_until='networkidle')
        image=self.page.locator('#quiet-moments .post-media img')
        expect(image).to_have_attribute('src',BASE+'/connectly/assets/image-fallback.svg')
        self.load_all_photos()

    def test_post_aspect_ratios_containment_and_even_action_targets(self):
        self.load()
        for width in [320,360,390,640,641,760,768,1023,1024,1440,1920]:
            with self.subTest(width=width):
                self.page.set_viewport_size({'width':width,'height':1000})
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                for card in self.page.locator('.post-card').all():
                    card_box=card.bounding_box()
                    if card.locator('.post-media').count():
                        media_box=card.locator('.post-media').bounding_box()
                        image_box=card.locator('.post-media img').bounding_box()
                        self.assertAlmostEqual(media_box['width']/media_box['height'],4/3 if width<=640 else 3/2,delta=.01)
                        self.assertGreaterEqual(media_box['x'],card_box['x'])
                        self.assertLessEqual(media_box['x']+media_box['width'],card_box['x']+card_box['width'])
                        self.assertAlmostEqual(image_box['height'],media_box['height'],delta=1)
                    actions=[button.bounding_box() for button in card.locator('.post-action').all()]
                    self.assertLess(max(b['width'] for b in actions)-min(b['width'] for b in actions),1)
                    self.assertTrue(all(b['height']>=44 for b in actions))
        self.page.locator('#post-text').fill('x'*1000)
        self.page.locator('#publish-post').click()
        self.page.set_viewport_size({'width':320,'height':700})
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))

    def test_branding_layout_and_subtle_hover_are_preserved(self):
        self.load()
        tokens=self.page.evaluate('''() => { const s=getComputedStyle(document.documentElement);return {bg:s.getPropertyValue('--bg').trim(),accent:s.getPropertyValue('--accent').trim(),font:s.getPropertyValue('--font').trim()}; }''')
        self.assertEqual(tokens['bg'],'#f8f9fb')
        self.assertEqual(tokens['accent'],'#e96e59')
        self.assertIn('Segoe UI',tokens['font'])
        self.assertEqual(len(self.page.locator('.app-layout').evaluate('(e)=>getComputedStyle(e).gridTemplateColumns').split()),3)
        self.page.mouse.move(0,0)
        before=self.page.locator('#quiet-moments').evaluate('(e)=>getComputedStyle(e).boxShadow')
        self.page.locator('#quiet-moments').hover()
        after=self.page.locator('#quiet-moments').evaluate('(e)=>getComputedStyle(e).boxShadow')
        self.assertNotEqual(before,after)


if __name__=='__main__':
    unittest.main(verbosity=2)
