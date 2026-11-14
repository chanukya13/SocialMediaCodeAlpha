import { feedService as service } from "./services/feed-service.js";
import { renderPost, renderComments, avatar } from "./components/post-card.js";
import {
  renderDiscovery,
  followButton,
} from "./components/discovery-sidebar.js";
import { updateNavigation } from "./components/navigation.js";
import { hydrateIcons, icon } from "./utils/icons.js";
import { escapeHTML as e, toast, scrollToTop } from "./utils/dom.js";
import { initializeImageFallbacks } from "./utils/images.js";

const state = {
  view: "home",
  filter: "for-you",
  query: "",
  sort: "latest",
  suggestionsExpanded: false,
  profile: null,
};
const $ = (selector) => document.querySelector(selector);
let attachedPhoto = null;
initializeImageFallbacks();
hydrateIcons();
$("#year").textContent = new Date().getFullYear();
function renderFeed() {
  const posts = service.getPosts(state);
  $("#feed").innerHTML = posts.length
    ? posts.map(renderPost).join("")
    : `<div class="empty-state card">${icon(state.view === "saved" ? "bookmark" : "search")}<h2>${state.view === "saved" && !state.query ? "A little space for your favorites" : "Nothing here just yet"}</h2><p>${state.query ? "Try a different name, topic, or phrase." : state.view === "saved" ? "Save a post that speaks to you. You’ll find it right here." : "Follow a few people to bring their stories into your feed."}</p><button class="primary-button" data-reset-feed>Explore the feed</button></div>`;
  $(".feed-end").hidden = !posts.length;
  $("#active-query").hidden = !state.query;
  $("#active-query>span").textContent = `Showing results for “${state.query}”`;
  $(".saved-count").textContent = service.savedCount();
  $(".sort-button>span:not([data-icon])").textContent =
    state.sort === "latest" ? "Latest" : "Popular";
  $("#sort-button").setAttribute(
    "aria-label",
    `Sort feed: ${state.sort === "latest" ? "latest first" : "most liked first"}`,
  );
}
function renderSidebar() {
  $("#discovery").innerHTML = renderDiscovery(state.suggestionsExpanded);
}
function setView(view, { resetQuery = true } = {}) {
  state.view = view;
  state.filter = "for-you";
  state.sort = view === "explore" ? "popular" : "latest";
  if (resetQuery) {
    state.query = "";
    $("#search-input").value = "";
  }
  document.querySelectorAll("[data-filter]").forEach((b) => {
    const active = b.dataset.filter === state.filter;
    b.classList.toggle("active", active);
    b.setAttribute("aria-pressed", active);
  });
  updateNavigation(view);
  renderFeed();
  scrollToTop();
}
function showProfile(id) {
  const u = service.getUser(id);
  if (!u) return;
  state.profile = id;
  $("#profile-content").innerHTML =
    `<div class="profile-cover"></div>${avatar(u, "profile-avatar")}<h2 id="profile-title">${e(u.name)}</h2><p class="profile-handle">@${e(u.handle)}</p><p class="profile-bio">${e(u.bio)}</p><div class="profile-facts"><span><strong>${e(u.followers)}</strong> followers</span><span><strong>${e(u.following)}</strong> following</span></div>${id === "you" ? '<p class="profile-demo">This is your mock profile. Profile editing will come in a later phase.</p>' : followButton(u)}<p class="profile-demo">Fictional profile · Connectly frontend preview</p>`;
  if (!$("#profile-dialog").open) $("#profile-dialog").showModal();
}
function refreshComposer() {
  const text = $("#post-text").value;
  $("#publish-post").disabled = !text.trim() && !attachedPhoto;
  $("#character-count").textContent =
    text.length > 800 ? `${text.length}/1000` : "";
}
function clearPhoto() {
  if (attachedPhoto) URL.revokeObjectURL(attachedPhoto);
  attachedPhoto = null;
  $("#post-photo").value = "";
  $("#attachment-preview").hidden = true;
  $("#attachment-image").removeAttribute("src");
  refreshComposer();
}

document.addEventListener("click", async (event) => {
  // Dismiss before delegated actions return (navigation, likes, profiles, etc.).
  if (!event.target.closest("#notifications,#notifications-button")) {
    $("#notifications").hidden = true;
    $("#notifications-button").setAttribute("aria-expanded", "false");
  }
  const viewButton = event.target.closest("[data-view]");
  if (viewButton) {
    setView(viewButton.dataset.view);
    return;
  }
  const filterButton = event.target.closest("[data-filter]");
  if (filterButton) {
    state.filter = filterButton.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((b) => {
      const active = b === filterButton;
      b.classList.toggle("active", active);
      b.setAttribute("aria-pressed", active);
    });
    renderFeed();
    return;
  }
  const profile = event.target.closest("[data-profile]");
  if (profile) {
    showProfile(profile.dataset.profile);
    return;
  }
  const follow = event.target.closest("[data-follow]");
  if (follow) {
    const id = follow.dataset.follow,
      followed = service.toggleFollow(id);
    follow.setAttribute("aria-pressed", followed);
    follow.setAttribute(
      "aria-label",
      `${followed ? "Unfollow" : "Follow"} ${service.getUser(id).name}`,
    );
    follow.textContent = followed ? "Following" : "+ Follow";
    document.querySelectorAll(`[data-follow="${id}"]`).forEach((b) => {
      b.setAttribute("aria-pressed", followed);
      b.setAttribute("aria-label", follow.getAttribute("aria-label"));
      b.textContent = follow.textContent;
    });
    if (state.filter === "following") renderFeed();
    toast(
      `${followed ? "Following" : "Unfollowed"} ${service.getUser(id).name}`,
    );
    return;
  }
  const action = event.target.closest("[data-action]");
  if (action) {
    const article = action.closest("[data-post-id]"),
      id = article.dataset.postId,
      post = service.getPost(id);
    switch (action.dataset.action) {
      case "like": {
        const liked = service.toggleLike(id);
        action.setAttribute("aria-pressed", liked);
        article.querySelector(".like-count").textContent =
          `${service.likeCount(post)} likes`;
        break;
      }
      case "bookmark": {
        const saved = service.toggleSaved(id);
        action.setAttribute("aria-pressed", saved);
        action.querySelector("span").textContent = saved ? "Saved" : "Save";
        $(".saved-count").textContent = service.savedCount();
        toast(
          saved
            ? "A little inspiration, saved for later."
            : "Post removed from your bookmarks.",
        );
        if (state.view === "saved" && !saved) renderFeed();
        break;
      }
      case "comments": {
        const panel = article.querySelector(".comments-panel");
        panel.hidden = !panel.hidden;
        action.setAttribute("aria-expanded", !panel.hidden);
        if (!panel.hidden)
          panel.querySelector("input").focus({ preventScroll: true });
        break;
      }
      case "share": {
        const url = new URL(location.href);
        url.hash = id;
        try {
          await navigator.clipboard.writeText(url.href);
          toast(
            post.userId === "you"
              ? "Link copied. This mock post is available only in this session."
              : "Post link copied. Pass a little inspiration along.",
          );
        } catch {
          toast("Copy the post link from the dialog.");
          window.prompt("Copy this post link:", url.href);
        }
        break;
      }
    }
    return;
  }
  const topic = event.target.closest("[data-topic]");
  if (topic) {
    state.query = topic.dataset.topic;
    $("#search-input").value = `#${state.query}`;
    setView("explore", { resetQuery: false });
    return;
  }
  if (event.target.closest("#toggle-suggestions")) {
    state.suggestionsExpanded = !state.suggestionsExpanded;
    renderSidebar();
    $("#toggle-suggestions").focus();
    return;
  }
  if (event.target.closest("[data-explore],[data-reset-feed]")) {
    setView("explore");
    return;
  }
  if (event.target.closest("[data-about],#about-button")) {
    $("#about-dialog").showModal();
    return;
  }
  const close = event.target.closest(".dialog-close,.dialog-done");
  if (close) {
    close.closest("dialog").close();
    return;
  }
});
document.addEventListener("submit", (event) => {
  const form = event.target.closest(".comment-form");
  if (!form) return;
  event.preventDefault();
  const input = form.elements.comment;
  const text = input.value.trim();
  if (!text) return;
  service.addComment(form.dataset.postId, text);
  const post = service.getPost(form.dataset.postId),
    article = form.closest("article");
  article.querySelector(".comments-panel").innerHTML = renderComments(post);
  article.querySelector(".comment-count").textContent =
    `${post.comments.length} ${post.comments.length === 1 ? "comment" : "comments"}`;
  article.querySelector(".comment-form input").focus({ preventScroll: true });
  toast("Your comment is part of the conversation.");
});
$("#post-text").addEventListener("input", refreshComposer);
$("#photo-button").addEventListener("click", () => $("#post-photo").click());
$("#emoji-button").addEventListener("click", () => {
  const input = $("#post-text");
  const emoji = " 😊";
  const nextLength =
    input.value.length -
    (input.selectionEnd - input.selectionStart) +
    emoji.length;
  if (nextLength > input.maxLength) {
    toast(`Posts are limited to ${input.maxLength} characters.`);
    return;
  }
  input.setRangeText(emoji, input.selectionStart, input.selectionEnd, "end");
  input.focus();
  refreshComposer();
});
$("#new-post").addEventListener("click", () => {
  setView("home");
  $("#post-text").focus();
});
$("#post-photo").addEventListener("change", () => {
  const file = $("#post-photo").files[0];
  if (!file) return;
  $("#composer-error").hidden = true;
  if (
    !["image/jpeg", "image/png", "image/webp"].includes(file.type) ||
    file.size > 5 * 1024 * 1024
  ) {
    $("#composer-error").textContent =
      "Choose a JPG, PNG, or WebP image under 5 MB.";
    $("#composer-error").hidden = false;
    $("#post-photo").value = "";
    return;
  }
  clearPhoto();
  attachedPhoto = URL.createObjectURL(file);
  $("#attachment-image").src = attachedPhoto;
  $("#attachment-preview").hidden = false;
  refreshComposer();
});
$("#attachment-image").addEventListener("error", () => {
  clearPhoto();
  $("#composer-error").textContent =
    "That image could not be read. Please choose another photo.";
  $("#composer-error").hidden = false;
});
$("#remove-photo").addEventListener("click", clearPhoto);
$("#publish-post").addEventListener("click", () => {
  if ($("#publish-post").disabled) return;
  service.createPost($("#post-text").value, attachedPhoto);
  attachedPhoto = null;
  $("#post-photo").value = "";
  $("#attachment-preview").hidden = true;
  $("#post-text").value = "";
  $("#composer-error").hidden = true;
  refreshComposer();
  setView("home");
  toast("Your moment, shared. Visible in this preview session.");
});
$("#sort-button").addEventListener("click", () => {
  state.sort = state.sort === "latest" ? "popular" : "latest";
  renderFeed();
});
$("#search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  state.query = $("#search-input").value.trim();
  renderFeed();
});
$("#search-input").addEventListener("input", () => {
  state.query = $("#search-input").value.trim();
  renderFeed();
});
$("#clear-query").addEventListener("click", () => {
  state.query = "";
  $("#search-input").value = "";
  renderFeed();
  $("#search-input").focus();
});
$("#notifications-button").addEventListener("click", () => {
  const panel = $("#notifications");
  panel.hidden = !panel.hidden;
  $("#notifications-button").setAttribute("aria-expanded", !panel.hidden);
  $(".notification-dot").hidden = true;
});
$("#back-to-top").addEventListener("click", scrollToTop);
document.addEventListener("keydown", (event) => {
  if (
    event.key === "/" &&
    !event.metaKey &&
    !event.ctrlKey &&
    !event.altKey &&
    !event.target.matches("input,textarea,[contenteditable]") &&
    !document.querySelector("dialog[open]")
  ) {
    event.preventDefault();
    $("#search-input").focus();
  }
  if (event.key === "Escape") {
    $("#notifications").hidden = true;
    $("#notifications-button").setAttribute("aria-expanded", "false");
  }
});
document.querySelectorAll("dialog").forEach((dialog) =>
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) {
      const rect = dialog.getBoundingClientRect();
      if (
        event.clientX < rect.left ||
        event.clientX > rect.right ||
        event.clientY < rect.top ||
        event.clientY > rect.bottom
      )
        dialog.close();
    }
  }),
);
renderSidebar();
renderFeed();
let initialId = "";
try {
  initialId = decodeURIComponent(location.hash.slice(1));
} catch {
  /* Ignore malformed shared fragments. */
}
if (service.getPost(initialId))
  requestAnimationFrame(() =>
    document.getElementById(initialId)?.scrollIntoView(),
  );
