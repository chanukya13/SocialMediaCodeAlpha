// Resolve dynamic assets from this module, independent of the document URL.
export function imageURL(filename) {
  return new URL(
    `../../assets/images/${encodeURIComponent(filename)}`,
    import.meta.url,
  ).href;
}

const fallbacks = {
  avatar: new URL("../../assets/avatar-fallback.svg", import.meta.url).href,
  post: new URL("../../assets/image-fallback.svg", import.meta.url).href,
};

// Original inline illustrations are a final safety net if the local fallback
// files cannot be fetched. No network requests or third-party services needed.
const inlineAvatar =
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"><rect width="80" height="80" rx="40" fill="#f5eee5"/><circle cx="40" cy="30" r="13" fill="#c8a68d"/><path d="M14 78v-8a26 26 0 0 1 52 0v8" fill="#c8a68d"/></svg>';
const inlinePost =
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500"><rect width="800" height="500" fill="#f5eee5"/><circle cx="590" cy="140" r="55" fill="#edc3a1"/><path d="M0 500 260 180 470 420 600 270 800 500" fill="#b9c5b6"/></svg>';

function recoverImage(image) {
  // The composer owns validation of a selected local file. Do not mask its error.
  if (!image.matches(".avatar, .post-media img")) return;
  const avatar = image.classList.contains("avatar");
  if (!image.dataset.fallback) {
    image.dataset.fallback = "local";
    image.alt = `${image.alt || (avatar ? "Profile photo" : "Post photo")} (image unavailable)`;
    image.src = avatar ? fallbacks.avatar : fallbacks.post;
  } else if (image.dataset.fallback === "local") {
    image.dataset.fallback = "inline";
    image.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(avatar ? inlineAvatar : inlinePost)}`;
  }
}

export function initializeImageFallbacks() {
  document.addEventListener(
    "error",
    (event) => {
      if (event.target instanceof HTMLImageElement) recoverImage(event.target);
    },
    true,
  );

  // Static avatars may have failed before deferred JavaScript became ready.
  document.querySelectorAll("img[src]").forEach((image) => {
    if (
      image.getAttribute("src") &&
      image.complete &&
      image.naturalWidth === 0
    ) {
      recoverImage(image);
    }
  });
}
