// Render colony-ad.html to MP4 frames (silent). Usage:
//   node render.js "<url with ?options>" <out.mp4|stills-dir> [stills]
const {chromium}=require('playwright');const {spawn}=require('child_process');
const [,,url,out,mode]=process.argv;
const H=url.includes('fmt=square')?1080:1920;
(async()=>{
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:H}});
 await p.goto(url,{waitUntil:'networkidle'});await p.evaluate(()=>window.READY);
 const total=await p.evaluate(()=>TOTAL);
 if(mode==='stills'){for(let k=0;k<10;k++){const t=+(total*(k+.75)/10).toFixed(2);await p.evaluate(t=>{render(t);return Promise.all([...document.querySelectorAll('img.clip')].map(i=>i.decode().catch(()=>0)))},t);await p.screenshot({path:`${out}/still-${String(k).padStart(2,'0')}.jpg`,type:'jpeg',quality:80});}await b.close();return;}
 const fps=30,N=Math.round(total*fps);
 const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',''+fps,'-c:v','mjpeg','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-preset','medium',out],{stdio:['pipe','inherit','inherit']});
 for(let i=0;i<N;i++){await p.evaluate(t=>{render(t);return Promise.all([...document.querySelectorAll('img.clip')].map(i=>i.decode().catch(()=>0)))},i/fps);const buf=await p.screenshot({type:'jpeg',quality:92});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));}
 ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();
})();
