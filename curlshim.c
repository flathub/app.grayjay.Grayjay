#include <stddef.h>

#if defined(_WIN32)
  #define SHIM_EXPORT __declspec(dllexport)
#else
  #define SHIM_EXPORT __attribute__((visibility("default")))
#endif

typedef struct Curl_easy CURL;
typedef int CURLcode;
typedef int CURLoption;
typedef int CURLINFO;
struct curl_slist;

extern CURL* curl_easy_init(void);
extern void  curl_easy_cleanup(CURL* h);
extern CURLcode curl_easy_perform(CURL* h);
extern CURLcode curl_global_init(long flags);
extern void  curl_global_cleanup(void);
extern const char *curl_easy_strerror(CURLcode c);
extern struct curl_slist *curl_slist_append(struct curl_slist* l, const char* s);
extern void  curl_slist_free_all(struct curl_slist* l);
extern CURLcode curl_easy_setopt(CURL* h, CURLoption opt, ...);
extern CURLcode curl_easy_getinfo(CURL* h, CURLINFO info, ...);
extern CURLcode curl_easy_impersonate(CURL* h, const char *target, int default_headers);

SHIM_EXPORT CURLcode ce_setopt_long(CURL* h, CURLoption opt, long v) { return curl_easy_setopt(h, opt, v); }
SHIM_EXPORT CURLcode ce_setopt_ptr(CURL* h, CURLoption opt, void *p) { return curl_easy_setopt(h, opt, p); }
SHIM_EXPORT CURLcode ce_setopt_str(CURL* h, CURLoption opt, const char *s) { return curl_easy_setopt(h, opt, s); }
SHIM_EXPORT CURL* ce_easy_init(void) { return curl_easy_init(); }
SHIM_EXPORT void ce_easy_cleanup(CURL* h) { curl_easy_cleanup(h); }
SHIM_EXPORT CURLcode ce_easy_perform(CURL* h) { return curl_easy_perform(h); }
SHIM_EXPORT CURLcode ce_global_init(long f) { return curl_global_init(f); }
SHIM_EXPORT void ce_global_cleanup(void) { curl_global_cleanup(); }
SHIM_EXPORT const char* ce_easy_strerror(CURLcode c) { return curl_easy_strerror(c); }
SHIM_EXPORT struct curl_slist* ce_slist_append(struct curl_slist* l, const char* s){ return curl_slist_append(l, s); }
SHIM_EXPORT void ce_slist_free_all(struct curl_slist* l) { curl_slist_free_all(l); }
SHIM_EXPORT CURLcode ce_easy_getinfo_ptr(CURL* h, CURLINFO i, void **p) { return curl_easy_getinfo(h, i, p); }
SHIM_EXPORT CURLcode ce_easy_getinfo_long(CURL* h, CURLINFO i, long *l) { return curl_easy_getinfo(h, i, l); }

SHIM_EXPORT CURLcode ce_easy_impersonate(CURL* h, const char *target, int def_headers) {
  return curl_easy_impersonate(h, target, def_headers);
}
