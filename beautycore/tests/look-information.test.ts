import test from 'node:test';
import assert from 'node:assert/strict';
import catalog from '../lib/business/style-catalog.json';
import { allServices } from '../lib/services';
import { publicStyle, resolveLookInformation } from '../lib/business/look-information';

test('all public style service options are exact catalog prices in the matching category', () => {
  const types = { hairstyle: 'hair', makeup: 'makeup', nails: 'nail' };
  for (const [feature, rows] of Object.entries(catalog))
    for (const [id, style] of Object.entries(rows)) {
      const info = resolveLookInformation(feature as keyof typeof types, id)!;
      assert.ok(info.description.length > 12);
      assert.equal(info.options.length, style.services.length);
      for (const option of info.options) {
        const service = allServices.find(
          (s) =>
            s.name === option.serviceName && s.serviceType === types[feature as keyof typeof types],
        );
        assert.ok(service);
        assert.equal(option.priceLabel, service.price);
      }
    }
});
test('from and per-nail prices keep their qualifiers; Makeup and unmapped curls do not invent prices', () => {
  const bun = resolveLookInformation('hairstyle', 'bun')!;
  assert.equal(bun.options.find((s) => s.serviceName === 'Bridal Hair')?.kind, 'from');
  const nails = resolveLookInformation('nails', 'french_tip')!;
  assert.deepEqual(
    nails.options.find((s) => s.serviceName === 'Nail Art (per nail)'),
    { serviceName: 'Nail Art (per nail)', amount: 50, priceLabel: 'Mula ₱50', kind: 'per_nail' },
  );
  const makeup = resolveLookInformation('makeup', 'natural_makeup')!;
  assert.equal(makeup.quoteRequired, true);
  assert.equal(makeup.options[0].amount, null);
  assert.equal(resolveLookInformation('hairstyle', 'perm_curls')?.options.length, 0);
  assert.equal(resolveLookInformation('hairstyle', 'wavy_hair')?.quoteRequired, true);
});
test('unknown/prototype names cannot become supported saves and price changes change the metadata version', () => {
  assert.equal(publicStyle('__proto__', 'crew_cut'), null);
  assert.equal(publicStyle('hairstyle', '__proto__'), null);
  assert.equal(resolveLookInformation('hairstyle', 'unsupported'), null);
  const old = resolveLookInformation('hairstyle', 'crew_cut')!;
  const service = allServices.find((s) => s.name === "Men's Cut")!;
  const price = service.price;
  try {
    service.price = '₱999';
    assert.notEqual(
      resolveLookInformation('hairstyle', 'crew_cut')!.catalogVersion,
      old.catalogVersion,
    );
  } finally {
    service.price = price;
  }
});
