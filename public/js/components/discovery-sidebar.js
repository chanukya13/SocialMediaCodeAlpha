import { users, suggestedIds, trends } from "../data/mock-data.js";
import { feedService } from "../services/feed-service.js";
import { avatar } from "./post-card.js";
import { icon } from "../utils/icons.js";
export function followButton(user) {
  const followed = feedService.isFollowing(user.id);
  return `<button class="follow-button" data-follow="${user.id}" aria-pressed="${followed}" aria-label="${followed ? "Unfollow" : "Follow"} ${user.name}">${followed ? "Following" : "+ Follow"}</button>`;
}
export function renderDiscovery(expanded = false) {
  return `<section class="discovery-card card"><div class="section-title"><h2>People to connect with</h2><button class="text-button" id="toggle-suggestions" aria-expanded="${expanded}">${expanded ? "Less" : "See all"}</button></div>${suggestedIds
    .slice(0, expanded ? 5 : 3)
    .map((id) => {
      const u = users[id];
      return `<div class="suggestion"><button class="suggestion-user" data-profile="${id}">${avatar(u)}<span><strong>${u.name}</strong><small>${u.role.split(" · ")[0].split(" & ")[0]}</small></span></button>${followButton(u)}</div>`;
    })
    .join("")}</section>
<section class="discovery-card card"><div class="section-title"><h2>Trending right now</h2>${icon("trending")}</div><p class="trending-intro">The conversations worth joining.</p>${trends.map((t, i) => `<button class="trending-item" data-topic="${t.tag}"><span class="trend-number">0${i + 1}</span><span class="trend-details"><small>${t.category}</small><strong>#${t.tag}</strong><span>${t.count}</span></span>${icon("trending")}</button>`).join("")}</section>
<section class="community-card"><span class="community-spark" aria-hidden="true">${icon("spark")}</span><div class="mini-avatars">${["maya", "james", "sophia"].map((id) => avatar(users[id])).join("")}<span>+2k</span></div><h2>Your people are here.</h2><p>A world of ideas, shared moments,<br>and people who just get you.</p><button data-explore>Find your inspiration ${icon("arrow-right")}</button></section>`;
}
