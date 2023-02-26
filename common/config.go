package common

import (
	"reflect"
	"strings"

	"github.com/spf13/viper"
)

// TODO: this won't be needed after https://github.com/spf13/viper/pull/1429
// from https://github.com/spf13/viper/issues/188#issuecomment-399884438
func AutoBindEnv(viper *viper.Viper, iface interface{}, parts ...string) {
	ifv := reflect.ValueOf(iface)
	ift := reflect.TypeOf(iface)
	for i := 0; i < ift.NumField(); i++ {
		v := ifv.Field(i)
		t := ift.Field(i)
		tv, ok := t.Tag.Lookup("mapstructure")
		if !ok {
			continue
		}
		switch v.Kind() {
		case reflect.Struct:
			AutoBindEnv(viper, v.Interface(), append(parts, tv)...)
		default:
			viper.BindEnv(strings.Join(append(parts, tv), "."))
		}
	}
}
