import { Screen, Panel, Body, Button, ErrorMessage, Loading } from '../components/ui';
import { useHealth } from '../lib/api/queries';
import { apiBaseUrl } from '../lib/config/environment';

export default function Settings() {
  const health = useHealth();
  return <Screen compact title="Your studio settings" description="A little care behind every look.">
    <Panel title="Studio connection" detail="Check the application connection on this device.">
      {health.isFetching && <Loading label="Checking connection…" />}
      {health.isError && <ErrorMessage message={health.error.message} />}
      {health.isSuccess && !health.isFetching && <Body>Connected · Your studio is available.</Body>}
      <Button label="Check connection" disabled={health.isFetching} onPress={() => void health.refetch()} />
      <Body muted>{apiBaseUrl || 'No application address configured.'}</Body>
    </Panel>
    <Panel title="Your photos, your choice">
      <Body>Selected photos stay local during this preview. Start Over removes the photo from that studio’s draft.</Body>
      <Body muted>Preview mode shows the original photo. Personal recommendations, generated results and Save/Share are awaiting integration.</Body>
    </Panel>
  </Screen>;
}
