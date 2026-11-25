const {chromium}=require('playwright');const {spawn}=require('child_process');
const [,,url,out,mode]=process.argv;
(async()=>{
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
 await p.goto(url,{waitUntil:'networkidle'});await p.evaluate(()=>document.fonts.ready);
 if(mode==='stills'){for(const t of [2.5,5.5,9,12.5,16,19.5,23,26,30]){await p.evaluate(t=>render(t),t);await p.screenshot({path:`${out}/still-${t}.jpg`,type:'jpeg',quality:80});}await b.close();return;}
 const fps=30,total=await p.evaluate(()=>TOTAL),N=Math.round(total*fps);
 const ff=spawn('ffmpeg',['-y','-f','image2pipe','-framerate',''+fps,'-c:v','mjpeg','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-preset','medium',out],{stdio:['pipe','inherit','inherit']});
 for(let i=0;i<N;i++){await p.evaluate(t=>render(t),i/fps);const buf=await p.screenshot({type:'jpeg',quality:92});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));}
 ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();
})();
