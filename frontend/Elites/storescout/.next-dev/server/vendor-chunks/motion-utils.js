"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
exports.id = "vendor-chunks/motion-utils";
exports.ids = ["vendor-chunks/motion-utils"];
exports.modules = {

/***/ "(ssr)/./node_modules/motion-utils/dist/es/format-error-message.mjs":
/*!********************************************************************!*\
  !*** ./node_modules/motion-utils/dist/es/format-error-message.mjs ***!
  \********************************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   formatErrorMessage: () => (/* binding */ formatErrorMessage)\n/* harmony export */ });\nfunction formatErrorMessage(message, errorCode) {\n    return errorCode\n        ? `${message}. For more information and steps for solving, visit https://motion.dev/troubleshooting/${errorCode}`\n        : message;\n}\n\n\n//# sourceMappingURL=format-error-message.mjs.map\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvbW90aW9uLXV0aWxzL2Rpc3QvZXMvZm9ybWF0LWVycm9yLW1lc3NhZ2UubWpzIiwibWFwcGluZ3MiOiI7Ozs7QUFBQTtBQUNBO0FBQ0EsYUFBYSxRQUFRLHlGQUF5RixVQUFVO0FBQ3hIO0FBQ0E7O0FBRThCO0FBQzlCIiwic291cmNlcyI6WyJDOlxcVXNlcnNcXGFzaHV0XzJ1cm5pYjBcXE9uZURyaXZlXFxEZXNrdG9wXFxFbGl0ZXNcXHN0b3Jlc2NvdXRcXG5vZGVfbW9kdWxlc1xcbW90aW9uLXV0aWxzXFxkaXN0XFxlc1xcZm9ybWF0LWVycm9yLW1lc3NhZ2UubWpzIl0sInNvdXJjZXNDb250ZW50IjpbImZ1bmN0aW9uIGZvcm1hdEVycm9yTWVzc2FnZShtZXNzYWdlLCBlcnJvckNvZGUpIHtcbiAgICByZXR1cm4gZXJyb3JDb2RlXG4gICAgICAgID8gYCR7bWVzc2FnZX0uIEZvciBtb3JlIGluZm9ybWF0aW9uIGFuZCBzdGVwcyBmb3Igc29sdmluZywgdmlzaXQgaHR0cHM6Ly9tb3Rpb24uZGV2L3Ryb3VibGVzaG9vdGluZy8ke2Vycm9yQ29kZX1gXG4gICAgICAgIDogbWVzc2FnZTtcbn1cblxuZXhwb3J0IHsgZm9ybWF0RXJyb3JNZXNzYWdlIH07XG4vLyMgc291cmNlTWFwcGluZ1VSTD1mb3JtYXQtZXJyb3ItbWVzc2FnZS5tanMubWFwXG4iXSwibmFtZXMiOltdLCJpZ25vcmVMaXN0IjpbMF0sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/motion-utils/dist/es/format-error-message.mjs\n");

/***/ }),

/***/ "(ssr)/./node_modules/motion-utils/dist/es/warn-once.mjs":
/*!*********************************************************!*\
  !*** ./node_modules/motion-utils/dist/es/warn-once.mjs ***!
  \*********************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   hasWarned: () => (/* binding */ hasWarned),\n/* harmony export */   warnOnce: () => (/* binding */ warnOnce)\n/* harmony export */ });\n/* harmony import */ var _format_error_message_mjs__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./format-error-message.mjs */ \"(ssr)/./node_modules/motion-utils/dist/es/format-error-message.mjs\");\n\n\nconst warned = new Set();\nfunction hasWarned(message) {\n    return warned.has(message);\n}\nfunction warnOnce(condition, message, errorCode) {\n    if (condition || warned.has(message))\n        return;\n    console.warn((0,_format_error_message_mjs__WEBPACK_IMPORTED_MODULE_0__.formatErrorMessage)(message, errorCode));\n    warned.add(message);\n}\n\n\n//# sourceMappingURL=warn-once.mjs.map\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvbW90aW9uLXV0aWxzL2Rpc3QvZXMvd2Fybi1vbmNlLm1qcyIsIm1hcHBpbmdzIjoiOzs7Ozs7QUFBZ0U7O0FBRWhFO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsaUJBQWlCLDZFQUFrQjtBQUNuQztBQUNBOztBQUUrQjtBQUMvQiIsInNvdXJjZXMiOlsiQzpcXFVzZXJzXFxhc2h1dF8ydXJuaWIwXFxPbmVEcml2ZVxcRGVza3RvcFxcRWxpdGVzXFxzdG9yZXNjb3V0XFxub2RlX21vZHVsZXNcXG1vdGlvbi11dGlsc1xcZGlzdFxcZXNcXHdhcm4tb25jZS5tanMiXSwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0IHsgZm9ybWF0RXJyb3JNZXNzYWdlIH0gZnJvbSAnLi9mb3JtYXQtZXJyb3ItbWVzc2FnZS5tanMnO1xuXG5jb25zdCB3YXJuZWQgPSBuZXcgU2V0KCk7XG5mdW5jdGlvbiBoYXNXYXJuZWQobWVzc2FnZSkge1xuICAgIHJldHVybiB3YXJuZWQuaGFzKG1lc3NhZ2UpO1xufVxuZnVuY3Rpb24gd2Fybk9uY2UoY29uZGl0aW9uLCBtZXNzYWdlLCBlcnJvckNvZGUpIHtcbiAgICBpZiAoY29uZGl0aW9uIHx8IHdhcm5lZC5oYXMobWVzc2FnZSkpXG4gICAgICAgIHJldHVybjtcbiAgICBjb25zb2xlLndhcm4oZm9ybWF0RXJyb3JNZXNzYWdlKG1lc3NhZ2UsIGVycm9yQ29kZSkpO1xuICAgIHdhcm5lZC5hZGQobWVzc2FnZSk7XG59XG5cbmV4cG9ydCB7IGhhc1dhcm5lZCwgd2Fybk9uY2UgfTtcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPXdhcm4tb25jZS5tanMubWFwXG4iXSwibmFtZXMiOltdLCJpZ25vcmVMaXN0IjpbMF0sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/motion-utils/dist/es/warn-once.mjs\n");

/***/ })

};
;