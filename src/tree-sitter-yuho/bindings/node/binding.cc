#include "nan.h"
#include "tree_sitter/parser.h"

extern "C" TSLanguage *tree_sitter_yuho();

namespace {

NAN_METHOD(New) {}

void Init(v8::Local<v8::Object> exports, v8::Local<v8::Object> module) {
  v8::Local<v8::FunctionTemplate> tpl = Nan::New<v8::FunctionTemplate>(New);
  tpl->SetClassName(Nan::New("Language").ToLocalChecked());
  tpl->InstanceTemplate()->SetInternalFieldCount(1);

  v8::Local<v8::Function> constructor = Nan::GetFunction(tpl).ToLocalChecked();
  v8::Local<v8::Object> instance =
      Nan::NewInstance(constructor, 0, nullptr).ToLocalChecked();
  Nan::SetInternalFieldPointer(instance, 0, tree_sitter_yuho());

  Nan::Set(instance, Nan::New("name").ToLocalChecked(),
           Nan::New("yuho").ToLocalChecked());
  Nan::Set(module, Nan::New("exports").ToLocalChecked(), instance);
}

NODE_MODULE(tree_sitter_yuho_binding, Init)

}  // namespace
