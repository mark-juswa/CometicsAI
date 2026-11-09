import { serviceLifecycle } from '../../../../../lib/business/api';
import { businessDependencies } from '../../../../../lib/business/server';
export const dynamic = 'force-dynamic';
async function route(request:Request,context:{params:Promise<{id:string}>}) {
 return serviceLifecycle(request,(await context.params).id,businessDependencies);
}
export {route as GET,route as POST};
