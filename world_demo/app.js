'use strict';
// Configure / Explore surface: a readable editorial journey, not a sales dashboard.
let language = 'fr';
let session = null;
let registry = null;
let archive = null;
let editions = null;
const screens = ['welcome','signup','offers','preview','activation','preferences','catalogue'];
const $ = selector => document.querySelector(selector);
const t = (fr, en) => language === 'fr' ? fr : en;
function node(tag, text, cls) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (cls) element.className = cls;
  return element;
}
async function api(path, payload) {
  const response = await fetch(path, payload === undefined ? {} : {
    method: 'POST', headers: {'Content-Type':'application/json','X-CSRF-Token':session.csrf},
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || String(response.status));
  return data;
}
function notice(text) { $('#notice').textContent = text; }
function translate() {
  document.documentElement.lang = language;
  document.title = t('WELISPEAK — Monde · Démonstration','WELISPEAK — World · Demonstration');
  document.querySelectorAll('[data-fr]').forEach(e => e.textContent = e.dataset[language]);
  document.querySelectorAll('[data-language]').forEach(e => e.setAttribute('aria-pressed', String(e.dataset.language === language)));
}
function renderSession() {
  $('#access-status').textContent = session.paid ? t('Monde · accès simulé actif','World · simulated access active') : t('Base gratuite · Monde verrouillé','Free base · World locked');
  $('#preferences-controls').disabled = !session.paid;
  $('#preferences-gate').textContent = session.paid ? t('Vos choix ne limitent pas le catalogue.','Your choices do not restrict the catalogue.') : t('Accès Monde requis. La case facultative ne débloque pas cet écran.','World access required. The optional checkbox does not unlock this screen.');
  $('#activate').disabled = !session.demo_enabled || !$('#confirm-activation').checked || session.paid;
  $('#activation-state').textContent = session.paid ? t('Activation de démonstration confirmée. Aucun paiement effectué.','Demonstration activation confirmed. No payment made.') : !session.demo_enabled ? t('Simulation désactivée côté serveur. Relancer avec --demo-activation pour l’autoriser.','Server simulation is disabled. Restart with --demo-activation to permit it.') : t('Cette action est une simulation, pas une preuve de paiement.','This action is a simulation, not proof of payment.');
  $('#mail-language').value = session.language;
  $('#discover').checked = session.discover_world;
  renderChoices(); renderMail();
}
function renderChoices() {
  const target = $('#choices'); target.replaceChildren();
  [registry.base,...registry.destinations].forEach(d => {
    const label = node('label',undefined,'check');
    const input = document.createElement('input');
    input.type = 'checkbox'; input.name = 'destination'; input.value = d.code;
    input.checked = session.destinations.includes(d.code);
    label.append(input,node('span', d[language])); target.append(label);
  });
}
function renderMail() {
  const names = [registry.base,...registry.destinations].filter(d => session.destinations.includes(d.code)).map(d => d[language]);
  const target = $('#mail-summary'); target.replaceChildren();
  target.append(node('h3',t('Votre sélection Monde','Your World selection')),
    node('p',names.join(' · ')),
    node('p',t('Langue du mail : ','Email language: ') + session.language.toUpperCase()),
    node('p',t('Présentation de format uniquement. Aucun article international réel dans ce mail.','Format preview only. No real international articles in this email.')));
}
function renderArchive() {
  const target = $('#archive'); target.replaceChildren();
  // Public CI archive only. All source caveats and dates travel with each item.
  archive.articles.forEach(article => {
    const copy = article[language];
    const block = node('article',undefined,'archive-article');
    block.append(node('p',copy.category,'eyebrow'), node('h2',copy.title));
    const image = document.createElement('img');
    image.src = '/assets/editorial-' + (article.icon + 1) + '.png';
    image.alt = t('Illustration générique : aucun événement précis représenté','Generic illustration: no specific event depicted');
    block.append(image,node('p',copy.summary),node('p',t('Les enjeux : ','Why it matters: ') + copy.relevance),node('p',copy.caveat,'caveat'),
      node('p',article.source + ' · ' + t('Publié : ','Published: ') + article.published_at + ' · ' + t('Événement : ','Event: ') + article.event_date,'meta'));
    const link = node('a', t('Source d’archive : ','Archived source: ') + article.source);
    link.href = article.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
    block.append(link); target.append(block);
  });
  const overview = $('#overview'); overview.replaceChildren();
  registry.destinations.forEach(d => overview.append(node('p',d[language] + ' · ' + d.code)));
}
async function renderCatalogue() {
  const target = $('#catalogue-list'); target.replaceChildren();
  $('#catalogue-gate').textContent = '';
  if (!session.paid) {
    $('#catalogue-gate').textContent = t('Accès protégé : activez la simulation Monde. L’aperçu public reste disponible.','Protected access: activate the World simulation. The public preview remains available.');
    return;
  }
  try {
    if (!editions) editions = (await api('/api/catalogue')).editions;
    editions.forEach(d => {
      const detail = document.createElement('details');
      detail.append(node('summary',d[language] + ' · ' + d.code));
      detail.append(node('p', t('DÉMONSTRATION · Aucune actualité du 1er novembre.','DEMONSTRATION · Not news for 1 November.'),'eyebrow'));
      if (d.code === 'CI') {
        detail.append(node('p',t('Archive du 22 octobre 2026, avec réserves et sources dans l’aperçu Côte d’Ivoire.','22 October 2026 archive, with caveats and sources in the Côte d’Ivoire preview.')));
        const link = node('a', t('Lire l’archive Côte d’Ivoire','Read the Côte d’Ivoire archive')); link.href = '#preview'; detail.append(link);
      } else detail.append(node('p',d['content_' + language]));
      target.append(detail);
    });
    $('#catalogue-gate').textContent = t('31 éditions accessibles · préférences mail sans effet sur l’accès.','31 editions accessible · email preferences do not affect access.');
  } catch (error) { notice(error.message); }
}
async function route() {
  let screen = location.hash.slice(1) || 'welcome';
  if (!screens.includes(screen)) screen = 'welcome';
  document.querySelectorAll('[data-screen]').forEach(e => e.hidden = e.dataset.screen !== screen);
  document.querySelectorAll('nav a').forEach(e => e.setAttribute('aria-current',e.hash === '#' + screen ? 'page' : 'false'));
  if (session && screen === 'catalogue') await renderCatalogue();
}
async function refresh() {
  translate(); renderSession(); renderArchive(); await route();
}
document.querySelectorAll('[data-language]').forEach(button => button.addEventListener('click', async () => {
  language = button.dataset.language; notice(''); await refresh();
}));
window.addEventListener('hashchange', () => { notice(''); route(); });
$('#signup-form').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    session = await api('/api/register',{discover_world:$('#discover').checked});
    renderSession();
    location.hash = session.discover_world ? '#offers' : '#welcome';
    // Hash navigation clears stale notices, then announce the outcome.
    setTimeout(() => notice(t('Inscription gratuite simulée. Aucun email stocké. La case Monde n’accorde aucun accès.','Free sign-up simulated. No email stored. The World checkbox grants no access.')),0);
  } catch (error) { notice(error.message); }
});
$('#confirm-activation').addEventListener('change',() => renderSession());
$('#activate').addEventListener('click', async () => {
  if (!$('#confirm-activation').checked) return;
  try {
    session = await api('/api/demo/activate',{confirm:true});
    editions = null; renderSession(); location.hash = '#preferences';
  } catch (error) { notice(error.message); }
});
$('#preferences-form').addEventListener('submit', async event => {
  event.preventDefault();
  const destinations = [...document.querySelectorAll('input[name=destination]:checked')].map(e => e.value);
  if (!destinations.length) return notice(t('Choisissez au moins une destination.','Choose at least one destination.'));
  try {
    session = await api('/api/preferences',{destinations,language:$('#mail-language').value});
    renderSession(); notice(t('Préférences enregistrées pour cette session de démonstration. Le catalogue conserve 31 éditions.','Preferences saved for this demonstration session. The catalogue still contains 31 editions.'));
  } catch (error) { notice(error.message); }
});
(async () => {
  try {
    [session,registry,archive] = await Promise.all([api('/api/session'),api('/api/overview'),api('/api/ci')]);
    await refresh();
  } catch (error) { notice(t('Serveur local indisponible : ','Local server unavailable: ') + error.message); }
})();
