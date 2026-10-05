import {mkdirSync,copyFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
mkdirSync('public/swagger',{recursive:true});
for (const file of ['swagger-ui-bundle.js','swagger-ui.css']) copyFileSync('node_modules/swagger-ui-dist/'+file,'public/swagger/'+file);
for (const [spec,out] of [['openapi','redoc'],['corgly','corgly-redoc']]) {
 copyFileSync('docs/openapi/'+spec+'.yaml','public/'+spec+'.yaml');
 execFileSync(process.execPath,['node_modules/@redocly/cli/bin/cli.js','build-docs','docs/openapi/'+spec+'.yaml','-o','public/'+out+'.html'],{stdio:'inherit'});
}
