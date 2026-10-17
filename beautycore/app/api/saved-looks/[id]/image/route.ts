import { savedLooks } from '../../../../../lib/business/api';
import { businessDependencies } from '../../../../../lib/business/server';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
type Context = { params: Promise<{ id: string }> };
const route = async (request: Request, context: Context) =>
  savedLooks(request, (await context.params).id, true, businessDependencies);
export { route as GET };
