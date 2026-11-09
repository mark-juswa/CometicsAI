import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight, BookOpen, Camera, Layers3, ScanFace } from 'lucide-react';

export const metadata: Metadata = {
  title: 'How our AI works',
  description: 'How BeautyCore trains its beauty adapters and creates Hair, Makeup and Nails previews from a client photo.',
};

const training = [
  ['Prepare examples', 'We prepare an original photo, a desired edited image and an instruction describing the change. Some edited targets are synthetic, so these are not all photographed salon before and after sessions.'],
  ['Review and separate', 'We review targets for style, identity, complexion and image quality. Training and validation use separate source identities or groups to check whether the learned changes transfer beyond the training examples.'],
  ['Train our adapters', 'We build on the pretrained FLUX.2 Klein Base 4B model and train specialized LoRA adapters. LoRA learns a smaller set of added weights that guides beauty edits while reusing the foundation model.'],
  ['Evaluate the results', 'We compare generated previews with the source and desired look. We review style visibility, complexion, facial details and nail boundaries before selecting an adapter or rendering approach for the app.'],
];
const inference = [
  ['Choose your photo', 'Upload a JPG or PNG, select an existing image, or use your camera. Capturing a photo does not start generation.'],
  ['Choose a supported look', 'Your selected style determines the editing instruction and the appropriate trained adapter or nail rendering configuration.'],
  ['Create the preview', 'For generated styles, the cloud GPU progressively constructs an edited image guided by your photo, the style instruction and the trained adapter. It does not simply paste a hairstyle picture onto your face.'],
  ['Review and decide', 'The app returns a preview for comparison. You can save a look or discuss it with a stylist. The result is a visual aid, not a guarantee of the same outcome in a salon.'],
];
function Steps({ items }: { items: string[][] }) {
  return <ol className="grid gap-4 sm:grid-cols-2">
    {items.map(([title, text], index) => <li key={title} className="border border-purple-light/20 bg-card p-6">
      <span className="text-xs font-semibold tracking-widest text-gold">0{index + 1}</span>
      <h3 className="mb-3 mt-3 font-serif text-2xl text-white">{title}</h3>
      <p className="text-sm leading-relaxed text-secondary">{text}</p>
    </li>)}
  </ol>;
}

export default function HowAiWorksPage() {
  return <article className="mx-auto max-w-6xl px-6 py-16 lg:px-10">
    <header className="mb-14 border-b border-purple-light/20 pb-12">
      <p className="mb-4 text-xs font-semibold uppercase tracking-[3px] text-gold">OUR AI METHODOLOGY</p>
      <h1 className="mb-6 max-w-3xl font-serif text-4xl text-white sm:text-6xl">How BeautyCore creates your preview.</h1>
      <p className="max-w-3xl text-base leading-relaxed text-secondary">We trained beauty specific adapters to work with an existing AI image model. Training happens before you use the app. Your photo is an input for a preview; uploading it does not retrain the model.</p>
      <div className="mt-7 flex flex-wrap gap-4 text-sm text-gold-light">
        <a href="#training" className="inline-flex items-center gap-2"><BookOpen size={17} aria-hidden="true" /> How we train</a>
        <a href="#your-preview" className="inline-flex items-center gap-2"><Camera size={17} aria-hidden="true" /> How your preview is made</a>
      </div>
    </header>

    <section id="training" aria-labelledby="training-title" className="scroll-mt-24 pb-14">
      <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-gold">BEFORE CLIENT USE</p>
      <h2 id="training-title" className="mb-4 font-serif text-3xl text-white sm:text-4xl">Our training process</h2>
      <p className="mb-7 max-w-3xl text-sm leading-relaxed text-secondary">Our contribution includes preparing paired examples, reviewing cosmetic targets, training task specific adapters, and integrating the trained outputs with preservation and application logic. We fine tune an existing foundation rather than train a large image model from scratch.</p>
      <Steps items={training} />
      <details className="mt-5 border border-purple-light/20 p-6 text-sm text-secondary">
        <summary className="cursor-pointer font-semibold text-gold-light">Technical training notes</summary>
        <div className="mt-4 space-y-4 leading-relaxed">
          <p>Each paired example supplies a source image, a target edit and an instruction. The training process uses these examples to optimize the adapter weights. The trained weights are saved and then reused during client generation.</p>
          <p>The corrective Makeup adapter completed 250 training updates using 52 reviewed pairs from 12 training identities. Its 26 validation pairs use two separate identities. Those validation identities were reused during development, so they are not an untouched final test set.</p>
          <p>We also compare foundation outputs and adapted outputs. A successful training run or a lower loss value alone does not establish realistic makeup or a good hairstyle.</p>
        </div>
      </details>
    </section>

    <section id="your-preview" aria-labelledby="preview-title" className="scroll-mt-24 border-t border-purple-light/20 py-14">
      <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-gold">WHEN YOU USE THE APP</p>
      <h2 id="preview-title" className="mb-7 font-serif text-3xl text-white sm:text-4xl">From your photo to your preview</h2>
      <Steps items={inference} />
    </section>

    <section aria-labelledby="features-title" className="border-t border-purple-light/20 py-14">
      <h2 id="features-title" className="mb-7 font-serif text-3xl text-white sm:text-4xl">Different features, different methods</h2>
      <div className="grid gap-5 md:grid-cols-3">
        <div className="border border-purple-light/20 bg-card p-6"><Layers3 className="mb-4 text-gold" aria-hidden="true" />
          <h3 className="mb-3 font-serif text-2xl text-white">Hair</h3><p className="text-sm leading-relaxed text-secondary">Two trained Hair adapters support the current 18 style catalog through selected instructions and profiles. Expanded options do not each represent a separately trained model.</p></div>
        <div className="border border-purple-light/20 bg-card p-6"><ScanFace className="mb-4 text-gold" aria-hidden="true" />
          <h3 className="mb-3 font-serif text-2xl text-white">Makeup</h3><p className="text-sm leading-relaxed text-secondary">One corrective Makeup adapter supports 13 coordinated looks. Style instructions cover eyes, lips, cheeks and complexion finish. Reviewed training targets aim to preserve the original person and complexion.</p></div>
        <div className="border border-purple-light/20 bg-card p-6"><Camera className="mb-4 text-gold" aria-hidden="true" />
          <h3 className="mb-3 font-serif text-2xl text-white">Nails</h3><p className="text-sm leading-relaxed text-secondary">Classic Red and Glossy Black use our trained nail adapter on localized crops. Six other designs use programmed rendering. Automatic hand localization and nail segmentation identify where to apply the result.</p></div>
      </div>
      <p className="mt-6 text-sm leading-relaxed text-secondary">The conversational consultant uses a separate text model to interpret preferences and recommend supported looks. It does not train the image adapters or paint the generated preview, and your consultation photo is not sent to that conversational model.</p>
    </section>

    <aside className="border border-gold/30 bg-card p-7" aria-labelledby="limits-title">
      <h2 id="limits-title" className="mb-3 font-serif text-2xl text-white">What to keep in mind</h2>
      <p className="text-sm leading-relaxed text-secondary">Hair and Makeup generate a portrait, so facial details, complexion or texture can still change. Instructions and reviewed examples help preservation but cannot guarantee it. Nails retain source pixels outside the final nail mask, and that protection depends on accurate mask placement. Lighting, pose and photo quality affect results.</p>
    </aside>
    <div className="mt-10 flex flex-wrap gap-5">
      <Link href="/client/ai-consultation" className="inline-flex items-center gap-2 rounded-sm bg-gold px-6 py-3 text-sm font-semibold text-deep">Explore the AI studio <ArrowRight size={16} aria-hidden="true" /></Link>
      <Link href="/about" className="self-center text-sm text-gold-light">About the clinic</Link>
    </div>
  </article>;
}
