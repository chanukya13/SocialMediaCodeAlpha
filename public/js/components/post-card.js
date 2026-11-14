import { feedService } from "../services/feed-service.js";
import { escapeHTML as e } from "../utils/dom.js";
import { icon } from "../utils/icons.js";
export function avatar(user, extra = "") {
  return `<img class="avatar ${extra}" src="assets/images/${e(user.avatar)}" alt="" width="42" height="42" loading="lazy">`;
}
export function renderComments(post) {
  return `<div class="comment-list">${
    post.comments.length
      ? post.comments
          .map((comment) => {
            const user = feedService.getUser(comment.userId);
            return `<div class="comment">${avatar(user)}<div class="comment-body"><strong>${e(user.name)}</strong><p>${e(comment.text)}</p></div></div>`;
          })
          .join("")
      : '<p class="no-comments">Be the first to start a conversation.</p>'
  }</div><form class="comment-form" data-post-id="${e(post.id)}"><label class="sr-only" for="comment-${e(post.id)}">Add a comment</label><input id="comment-${e(post.id)}" name="comment" placeholder="Add to the conversation…" maxlength="500" required autocomplete="off"><button type="submit" aria-label="Send comment">${icon("send")}</button></form>`;
}
export function renderPost(post) {
  const user = feedService.getUser(post.userId),
    liked = feedService.isLiked(post.id),
    saved = feedService.isSaved(post.id);
  const src = post.image?.startsWith("blob:")
    ? post.image
    : `assets/images/${post.image}`;
  return `<article class="post-card card" id="${e(post.id)}" data-post-id="${e(post.id)}" aria-label="Post by ${e(user.name)}">
<div class="post-top"><button class="post-author" data-profile="${e(user.id)}">${avatar(user)}<span><span class="author-name">${e(user.name)}${user.verified ? `<span class="verified" aria-label="Verified mock profile">${icon("verified")}</span>` : ""}</span><span class="author-meta">@${e(user.handle)} <span>·</span> ${e(post.time)} <span>·</span> ${icon("globe")}</span></span></button><span class="post-topic">${e(post.topic)}</span></div>
<p class="post-copy">${e(post.text)}${post.hashtags.length ? `\n<span class="hashtag">${post.hashtags.map((t) => `#${e(t)}`).join(" ")}</span>` : ""}</p>
${post.image ? `<div class="post-media"><img src="${e(src)}" alt="${e(post.imageAlt)}" width="900" height="540" ${post.order === 4 ? 'fetchpriority="high"' : 'loading="lazy"'}>${post.caption ? `<span class="image-caption">${e(post.caption)}</span>` : ""}</div>` : ""}
<div class="post-stats"><span class="reactions"><span class="reaction-bubbles" aria-hidden="true"><span>♥</span><span>✦</span></span><span class="like-count">${feedService.likeCount(post)} likes</span></span><span class="comment-count">${post.comments.length} ${post.comments.length === 1 ? "comment" : "comments"}</span></div>
<div class="post-actions"><button class="post-action" data-action="like" aria-pressed="${liked}" aria-label="Like post by ${e(user.name)}">${icon("heart")}<span>Like</span></button><button class="post-action" data-action="comments" aria-expanded="false" aria-controls="comments-${e(post.id)}">${icon("comment")}<span>Comment</span></button><button class="post-action" data-action="share" aria-label="Copy link to post by ${e(user.name)}">${icon("share")}<span>Share</span></button><button class="post-action" data-action="bookmark" aria-pressed="${saved}" aria-label="Bookmark post by ${e(user.name)}">${icon("bookmark")}<span>${saved ? "Saved" : "Save"}</span></button></div>
<section class="comments-panel" id="comments-${e(post.id)}" aria-label="Comments on ${e(user.name)}'s post" hidden>${renderComments(post)}</section>
</article>`;
}
