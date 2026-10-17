import { bookingApi } from '../../../lib/business/api';
import { businessDependencies } from '../../../lib/business/server';
export const dynamic = 'force-dynamic';
const route = (request: Request) => bookingApi(request, undefined, businessDependencies);
export { route as GET, route as POST };
