"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
exports.id = "vendor-chunks/motion-dom";
exports.ids = ["vendor-chunks/motion-dom"];
exports.modules = {

/***/ "(ssr)/./node_modules/motion-dom/dist/es/render/utils/reduced-motion/index.mjs":
/*!*******************************************************************************!*\
  !*** ./node_modules/motion-dom/dist/es/render/utils/reduced-motion/index.mjs ***!
  \*******************************************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   hasReducedMotionListener: () => (/* reexport safe */ _state_mjs__WEBPACK_IMPORTED_MODULE_0__.hasReducedMotionListener),\n/* harmony export */   initPrefersReducedMotion: () => (/* binding */ initPrefersReducedMotion),\n/* harmony export */   prefersReducedMotion: () => (/* reexport safe */ _state_mjs__WEBPACK_IMPORTED_MODULE_0__.prefersReducedMotion)\n/* harmony export */ });\n/* harmony import */ var _state_mjs__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./state.mjs */ \"(ssr)/./node_modules/motion-dom/dist/es/render/utils/reduced-motion/state.mjs\");\n\n\nconst isBrowser = typeof window !== \"undefined\";\nfunction initPrefersReducedMotion() {\n    _state_mjs__WEBPACK_IMPORTED_MODULE_0__.hasReducedMotionListener.current = true;\n    if (!isBrowser)\n        return;\n    if (window.matchMedia) {\n        const motionMediaQuery = window.matchMedia(\"(prefers-reduced-motion)\");\n        const setReducedMotionPreferences = () => (_state_mjs__WEBPACK_IMPORTED_MODULE_0__.prefersReducedMotion.current = motionMediaQuery.matches);\n        motionMediaQuery.addEventListener(\"change\", setReducedMotionPreferences);\n        setReducedMotionPreferences();\n    }\n    else {\n        _state_mjs__WEBPACK_IMPORTED_MODULE_0__.prefersReducedMotion.current = false;\n    }\n}\n\n\n//# sourceMappingURL=index.mjs.map\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvbW90aW9uLWRvbS9kaXN0L2VzL3JlbmRlci91dGlscy9yZWR1Y2VkLW1vdGlvbi9pbmRleC5tanMiLCJtYXBwaW5ncyI6Ijs7Ozs7OztBQUE2RTs7QUFFN0U7QUFDQTtBQUNBLElBQUksZ0VBQXdCO0FBQzVCO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsbURBQW1ELDREQUFvQjtBQUN2RTtBQUNBO0FBQ0E7QUFDQTtBQUNBLFFBQVEsNERBQW9CO0FBQzVCO0FBQ0E7O0FBRW9GO0FBQ3BGIiwic291cmNlcyI6WyJDOlxcVXNlcnNcXGFzaHV0XzJ1cm5pYjBcXE9uZURyaXZlXFxEZXNrdG9wXFxFbGl0ZXNcXHN0b3Jlc2NvdXRcXG5vZGVfbW9kdWxlc1xcbW90aW9uLWRvbVxcZGlzdFxcZXNcXHJlbmRlclxcdXRpbHNcXHJlZHVjZWQtbW90aW9uXFxpbmRleC5tanMiXSwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0IHsgaGFzUmVkdWNlZE1vdGlvbkxpc3RlbmVyLCBwcmVmZXJzUmVkdWNlZE1vdGlvbiB9IGZyb20gJy4vc3RhdGUubWpzJztcblxuY29uc3QgaXNCcm93c2VyID0gdHlwZW9mIHdpbmRvdyAhPT0gXCJ1bmRlZmluZWRcIjtcbmZ1bmN0aW9uIGluaXRQcmVmZXJzUmVkdWNlZE1vdGlvbigpIHtcbiAgICBoYXNSZWR1Y2VkTW90aW9uTGlzdGVuZXIuY3VycmVudCA9IHRydWU7XG4gICAgaWYgKCFpc0Jyb3dzZXIpXG4gICAgICAgIHJldHVybjtcbiAgICBpZiAod2luZG93Lm1hdGNoTWVkaWEpIHtcbiAgICAgICAgY29uc3QgbW90aW9uTWVkaWFRdWVyeSA9IHdpbmRvdy5tYXRjaE1lZGlhKFwiKHByZWZlcnMtcmVkdWNlZC1tb3Rpb24pXCIpO1xuICAgICAgICBjb25zdCBzZXRSZWR1Y2VkTW90aW9uUHJlZmVyZW5jZXMgPSAoKSA9PiAocHJlZmVyc1JlZHVjZWRNb3Rpb24uY3VycmVudCA9IG1vdGlvbk1lZGlhUXVlcnkubWF0Y2hlcyk7XG4gICAgICAgIG1vdGlvbk1lZGlhUXVlcnkuYWRkRXZlbnRMaXN0ZW5lcihcImNoYW5nZVwiLCBzZXRSZWR1Y2VkTW90aW9uUHJlZmVyZW5jZXMpO1xuICAgICAgICBzZXRSZWR1Y2VkTW90aW9uUHJlZmVyZW5jZXMoKTtcbiAgICB9XG4gICAgZWxzZSB7XG4gICAgICAgIHByZWZlcnNSZWR1Y2VkTW90aW9uLmN1cnJlbnQgPSBmYWxzZTtcbiAgICB9XG59XG5cbmV4cG9ydCB7IGhhc1JlZHVjZWRNb3Rpb25MaXN0ZW5lciwgaW5pdFByZWZlcnNSZWR1Y2VkTW90aW9uLCBwcmVmZXJzUmVkdWNlZE1vdGlvbiB9O1xuLy8jIHNvdXJjZU1hcHBpbmdVUkw9aW5kZXgubWpzLm1hcFxuIl0sIm5hbWVzIjpbXSwiaWdub3JlTGlzdCI6WzBdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/motion-dom/dist/es/render/utils/reduced-motion/index.mjs\n");

/***/ }),

/***/ "(ssr)/./node_modules/motion-dom/dist/es/render/utils/reduced-motion/state.mjs":
/*!*******************************************************************************!*\
  !*** ./node_modules/motion-dom/dist/es/render/utils/reduced-motion/state.mjs ***!
  \*******************************************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   hasReducedMotionListener: () => (/* binding */ hasReducedMotionListener),\n/* harmony export */   prefersReducedMotion: () => (/* binding */ prefersReducedMotion)\n/* harmony export */ });\n// Does this device prefer reduced motion? Returns `null` server-side.\nconst prefersReducedMotion = { current: null };\nconst hasReducedMotionListener = { current: false };\n\n\n//# sourceMappingURL=state.mjs.map\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvbW90aW9uLWRvbS9kaXN0L2VzL3JlbmRlci91dGlscy9yZWR1Y2VkLW1vdGlvbi9zdGF0ZS5tanMiLCJtYXBwaW5ncyI6Ijs7Ozs7QUFBQTtBQUNBLCtCQUErQjtBQUMvQixtQ0FBbUM7O0FBRXVCO0FBQzFEIiwic291cmNlcyI6WyJDOlxcVXNlcnNcXGFzaHV0XzJ1cm5pYjBcXE9uZURyaXZlXFxEZXNrdG9wXFxFbGl0ZXNcXHN0b3Jlc2NvdXRcXG5vZGVfbW9kdWxlc1xcbW90aW9uLWRvbVxcZGlzdFxcZXNcXHJlbmRlclxcdXRpbHNcXHJlZHVjZWQtbW90aW9uXFxzdGF0ZS5tanMiXSwic291cmNlc0NvbnRlbnQiOlsiLy8gRG9lcyB0aGlzIGRldmljZSBwcmVmZXIgcmVkdWNlZCBtb3Rpb24/IFJldHVybnMgYG51bGxgIHNlcnZlci1zaWRlLlxuY29uc3QgcHJlZmVyc1JlZHVjZWRNb3Rpb24gPSB7IGN1cnJlbnQ6IG51bGwgfTtcbmNvbnN0IGhhc1JlZHVjZWRNb3Rpb25MaXN0ZW5lciA9IHsgY3VycmVudDogZmFsc2UgfTtcblxuZXhwb3J0IHsgaGFzUmVkdWNlZE1vdGlvbkxpc3RlbmVyLCBwcmVmZXJzUmVkdWNlZE1vdGlvbiB9O1xuLy8jIHNvdXJjZU1hcHBpbmdVUkw9c3RhdGUubWpzLm1hcFxuIl0sIm5hbWVzIjpbXSwiaWdub3JlTGlzdCI6WzBdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/motion-dom/dist/es/render/utils/reduced-motion/state.mjs\n");

/***/ })

};
;