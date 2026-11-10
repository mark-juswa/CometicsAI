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
      const names = info.options.map((option) => option.serviceName);
      if (feature === 'hairstyle') {
        assert.equal(new Set(names).size, names.length);
        assert.ok(!names.includes("Men's Cut"));
        assert.deepEqual(info.options.slice(0, 2).map(({ serviceName, amount }) => [serviceName, amount]), [
          ["Women's Cut & Blowdry", 350],
          ['Blowdry & Style', 250],
        ]);
        for (const serviceName of style.services.filter((name) => name !== "Men's Cut"))
          assert.ok(names.includes(serviceName));
      } else {
        assert.deepEqual(names, style.services);
      }
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
test('estimates keep price qualifiers and list optional colour without inventing a curl price', () => {
  const bun = resolveLookInformation('hairstyle', 'bun')!;
  assert.equal(bun.options.find((s) => s.serviceName === 'Bridal Hair')?.kind, 'from');
  assert.deepEqual(bun.options.find((s) => s.serviceName === 'Full Colour'), {
    serviceName: 'Full Colour', amount: 800, priceLabel: 'Mula ₱800', kind: 'from',
  });
  assert.match(bun.note, /Colour services are optional\. The salon confirms your final price\./);
  const nails = resolveLookInformation('nails', 'french_tip')!;
  assert.deepEqual(
    nails.options.find((s) => s.serviceName === 'Nail Art (per nail)'),
    { serviceName: 'Nail Art (per nail)', amount: 50, priceLabel: 'Mula ₱50', kind: 'per_nail' },
  );
  const makeup = resolveLookInformation('makeup', 'natural_makeup')!;
  assert.equal(makeup.quoteRequired, true);
  assert.equal(makeup.options[0].amount, null);
  assert.ok(!resolveLookInformation('hairstyle', 'perm_curls')!.options.some((s) => /perm/i.test(s.serviceName)));
  assert.ok(!resolveLookInformation('hairstyle', 'wavy_hair')!.options.some((s) => /wav/i.test(s.serviceName)));
});
test('unknown/prototype names cannot become supported saves and price changes change the metadata version', () => {
  assert.equal(publicStyle('__proto__', 'crew_cut'), null);
  assert.equal(publicStyle('hairstyle', '__proto__'), null);
  assert.equal(resolveLookInformation('hairstyle', 'unsupported'), null);
  const old = resolveLookInformation('hairstyle', 'crew_cut')!;
  const service = allServices.find((s) => s.name === "Women's Cut & Blowdry")!;
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
