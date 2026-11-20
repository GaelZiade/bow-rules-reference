const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + __dirname + '/srd_print.html', { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const foot = '<div style="width:100%;font-family:Georgia,serif;font-size:8px;color:#8a8ea0;padding:0 0.8in;display:flex;justify-content:space-between"><span>Bleach: Online World — Rules Reference</span><span class="pageNumber"></span></div>';
  await p.pdf({ path: 'srd.pdf', printBackground: true, outline: true, tagged: true, preferCSSPageSize: true,
    displayHeaderFooter: true, headerTemplate: '<div></div>', footerTemplate: foot });
  await p.pdf({ path: 'srd_cover.pdf', printBackground: true, preferCSSPageSize: true, pageRanges: '1' });
  console.log('fonts', await p.evaluate(() => [...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family).join(',')));
  await b.close();
})();
