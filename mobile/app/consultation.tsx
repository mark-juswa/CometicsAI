import { router } from 'expo-router';
import { Screen, Panel, Body, Button } from '../components/ui';
import { consultationStages } from '../features/consultation/overview';
import { services } from '../constants/services';
import { featureIds } from '../lib/api/contracts';

export default function Consultation() {
  return <Screen title="A look that" emphasis="feels like you." description="Choose a service to explore your next direction.">
    <Panel title="Your consultation" detail={consultationStages.join(' → ')}>
      <Body>Consultation overview · Recommendations and generated looks will be available in a later phase.</Body>
      <Body muted>For now, choose a service to explore its live catalog and your local preview.</Body>
      {featureIds.map(id => <Button key={id} label={services[id].label} secondary onPress={() => router.push(services[id].route)} />)}
    </Panel>
  </Screen>;
}
