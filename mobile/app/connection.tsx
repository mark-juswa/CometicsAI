import { Screen, Panel, Body, Button, ErrorMessage, Loading } from '../components/ui';
import { useHealth } from '../lib/api/queries';
import { apiBaseUrl } from '../lib/config/environment';

export default function Connection() {
  const health = useHealth();
  return <Screen title="Your studio," emphasis="connected." description="Check that this device can reach the application API.">
    <Panel title="Application API">
      <Body>{apiBaseUrl || 'No API address configured.'}</Body>
      {health.isFetching && <Loading label="Checking connection…" />}
      {health.isError && <ErrorMessage message={health.error.message} />}
      {health.isSuccess && !health.isFetching && <>
        <Body>Connected · {health.data.status}</Body><Body muted>Backend generator: {health.data.generator}</Body>
        <Body muted>This checks API connectivity. It does not run generation or prove GPU readiness.</Body>
      </>}
      <Button label="Check connection" disabled={health.isFetching} onPress={() => void health.refetch()} />
    </Panel>
  </Screen>;
}
