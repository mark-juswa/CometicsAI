import { savedLooks } from '../../../lib/business/api';
import { businessDependencies } from '../../../lib/business/server';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
const route = (request: Request) => savedLooks(request, undefined, false, businessDependencies);
export { route as GET, route as POST };
