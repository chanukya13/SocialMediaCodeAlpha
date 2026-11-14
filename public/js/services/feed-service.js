import { initialPosts, users } from "../data/mock-data.js";
// Data boundary: replace these methods with API calls in a future phase.
const storageKey = "connectly.preferences.v1";
let stored = {};
try {
  stored = JSON.parse(localStorage.getItem(storageKey)) || {};
} catch {
  /* Storage may be unavailable. */
}
const posts = structuredClone(initialPosts);
const validPostIds = new Set(posts.map((p) => p.id));
const safeList = (value, valid) =>
  Array.isArray(value)
    ? value.filter((id) => typeof id === "string" && valid.has(id))
    : [];
const liked = new Set(safeList(stored.liked, validPostIds));
const saved = new Set(safeList(stored.saved, validPostIds));
const followed = new Set(
  safeList(
    stored.followed ?? ["maya"],
    new Set(Object.keys(users).filter((id) => id !== "you")),
  ),
);
function persist() {
  try {
    localStorage.setItem(
      storageKey,
      JSON.stringify({
        liked: [...liked],
        saved: [...saved],
        followed: [...followed],
      }),
    );
  } catch {
    /* Interactions remain usable in memory. */
  }
}
export const feedService = {
  getUser(id) {
    return users[id];
  },
  getPosts({
    view = "home",
    filter = "for-you",
    query = "",
    sort = "latest",
  } = {}) {
    const needle = query.trim().toLowerCase().replace(/^#/, "");
    return posts
      .filter(
        (p) =>
          (view !== "saved" || saved.has(p.id)) &&
          (filter !== "following" ||
            followed.has(p.userId) ||
            p.userId === "you") &&
          (!needle ||
            [
              p.text,
              p.topic,
              ...p.hashtags,
              users[p.userId].name,
              users[p.userId].handle,
            ]
              .join(" ")
              .toLowerCase()
              .includes(needle)),
      )
      .sort((a, b) =>
        sort === "popular"
          ? this.likeCount(b) - this.likeCount(a) || b.order - a.order
          : b.order - a.order,
      );
  },
  getPost(id) {
    return posts.find((p) => p.id === id);
  },
  isLiked(id) {
    return liked.has(id);
  },
  isSaved(id) {
    return saved.has(id);
  },
  isFollowing(id) {
    return followed.has(id);
  },
  savedCount() {
    return saved.size;
  },
  likeCount(post) {
    return post.likes + Number(liked.has(post.id));
  },
  toggleLike(id) {
    if (!this.getPost(id)) return false;
    liked.has(id) ? liked.delete(id) : liked.add(id);
    persist();
    return liked.has(id);
  },
  toggleSaved(id) {
    if (!this.getPost(id)) return false;
    saved.has(id) ? saved.delete(id) : saved.add(id);
    persist();
    return saved.has(id);
  },
  toggleFollow(id) {
    if (!users[id] || id === "you") return false;
    followed.has(id) ? followed.delete(id) : followed.add(id);
    persist();
    return followed.has(id);
  },
  createPost(text, image) {
    const post = {
      id: `post-${crypto.randomUUID()}`,
      userId: "you",
      time: "Just now",
      order: Date.now(),
      topic: "Your moment",
      text: text.trim(),
      hashtags: [],
      image,
      imageAlt: "Photo shared by Alex Morgan",
      likes: 0,
      comments: [],
    };
    posts.unshift(post);
    return post;
  },
  addComment(id, text) {
    const post = this.getPost(id);
    if (!post || !text.trim()) return;
    post.comments.push({
      id: crypto.randomUUID(),
      userId: "you",
      text: text.trim(),
    });
  },
};
