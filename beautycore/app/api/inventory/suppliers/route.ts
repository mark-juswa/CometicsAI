import {inventoryApi} from '@/lib/business/inventory';
import {businessDependencies} from '@/lib/business/server';
import {databaseSql} from '@/db';
export const dynamic='force-dynamic';
const route=(request:Request)=>inventoryApi(request,"suppliers",{actor:businessDependencies.actor,publicOrigin:businessDependencies.publicOrigin,query:(text,values=[])=>databaseSql.query(text,values)});
export {route as GET,route as POST,route as PATCH};
