import { bookingApi } from '../../../../lib/business/api';
import { businessDependencies } from '../../../../lib/business/server';
export const dynamic = 'force-dynamic';
type Context = { params: Promise<{ id: string }> };
const route = async (request: Request, context: Context) =>
  bookingApi(request, (await context.params).id, businessDependencies);
export { route as GET, route as PATCH, route as DELETE };
