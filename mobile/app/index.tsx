import { router } from 'expo-router';
import { Screen, Panel, Body, Button, ErrorMessage, Loading } from '../components/ui';
import { services } from '../constants/services';
import { featureIds } from '../lib/api/contracts';
import { useFeatures } from '../lib/api/queries';

export default function Home() {
  const features = useFeatures();
  return <Screen title="Your look," emphasis="reimagined." description="ANDREA’S AESTHETIC & WELLNESS CLINIC · Explore your beauty studio.">
    <Panel title="Choose your service" detail="Find a look that feels like you.">
      {features.isFetching && <Loading label="Loading services…" />}
      {features.isError && <ErrorMessage message={features.error.message} retry={() => void features.refetch()} />}
      {features.data?.length === 0 && <Body>No services are available from this API.</Body>}
      {featureIds.map(id => {
        const service = services[id];
        const remote = features.data?.find(row => row.id === id);
        return <Panel key={id} title={service.label} detail={remote?.description ?? service.description}>
          <Button label={`Explore ${service.label}`} secondary onPress={() => router.push(service.route)} />
        </Panel>;
      })}
    </Panel>
    <Panel title="A little guidance" detail="Service · Direction · Your Looks">
      <Body>Explore the Consultation stages. Personal recommendations will be connected in a later phase.</Body>
      <Button label="Consultation" secondary onPress={() => router.push('/consultation')} />
    </Panel>
    <Button label="Check API connection" secondary onPress={() => router.push('/connection')} />
  </Screen>;
}
