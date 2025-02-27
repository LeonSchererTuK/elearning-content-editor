<template>
  <!-- Toolbar -->
  <div
    class="card"
    :class="{
      lightmode: colorMode === 'light',
      darkmode: colorMode !== 'light',
    }"
  >
    <div
      class="flex overflow-hidden w-full h-6rem justify-content-around"
      :class="{
        lightmode: colorMode === 'light',
        darkmode: colorMode !== 'light',
      }"
    >
      <!-- Logo -->
      <div
        class="flex-none flex align-items-center justify-content-center ml-4 m-1 w-3rem"
      >
        <slot name="logo"></slot>
      </div>
      <!-- AppName. Only visible if Desktop -->
      <div
        v-if="!mobile"
        class="flex-none flex align-items-center justify-content-center m-1"
      >
        <slot name="appname"></slot>
      </div>
      <!-- First Items -->
      <div class="flex-none flex align-items-center justify-content-center m-1">
        <slot name="start"></slot>
      </div>
      <!-- Center Items. Only visible if Desktop -->
      <div
        v-if="!mobile"
        class="flex-grow-1 flex align-items-center align-items-center justify-content-center m-1"
      >
        <slot name="center"></slot>
      </div>
      <!-- Last Items. Only visible if Desktop -->
      <div
        class="flex-none flex align-items-center align-items-center justify-content-center m-1"
      >
        <slot name="before-end"></slot>
      </div>
      <!-- Menu Items. Will be behind a menu if not Desktop -->
      <div
        class="flex-none flex align-items-center align-items-center justify-content-center m-1"
      >
        <!-- Desktop Menu -->
        <div
          v-if="!mobile"
          class="desktop-submenu-list flex gap-3 align-items-center m-3"
        >
          <slot name="end"></slot>
          <DarkModeToggle />
          <Button icon="fa-solid fa-right-from-bracket" @click="logout" />
        </div>

        <!-- Mobile Menu -->
        <div
          v-if="mobile"
          class="cursor-pointer"
          @click="showEndMenu = !showEndMenu"
        >
          <i class="fa-solid fa-bars text-3xl"></i>
        </div>

        <div
          v-if="mobile && showEndMenu"
          class="absolute right-0 surface-10 border-round-xl rounded-md shadow-lg w-full p-3 shadow-3 z-1 flex flex-column gap-2"
          :class="{
            'bg-white': colorMode === 'light',
            'surface-100': colorMode !== 'light',
          }"
          style="top: 5rem; min-height: calc(100vh - 5rem)"
        >
          <div class="flex justify-content-end align-items-center">
            <slot name="before-end"></slot>
            <slot name="end"></slot>
            <DarkModeToggle />
            <Button
              class="ml-3"
              icon="fa-solid fa-right-from-bracket"
              @click="logout"
            />
          </div>

          <div class="flex flex-column flex-grow-1">
            <slot name="sidebar" />
          </div>

          <div>
            <slot name="submenu"></slot>
          </div>

          <!-- <ul class="m-0 list-none mobile-submenu-list">
            <li class="flex justify-space-between">
              <div class="flex">
                <slot name="before-end"></slot>
              </div>

              <div>
                <slot name="end"></slot>
              </div>

              <DarkModeToggle />
            </li>

            <slot name="sidebar" />
          </ul> -->
        </div>
      </div>
    </div>
  </div>

  <!-- sidebar and Content -->
  <div
    class="app-layout__content p-2 flex-grow-1"
    :class="{
      lightmode: colorMode === 'light',
      darkmode: colorMode !== 'light',
      showSidebar: showSidebar && !!slots.sidebar,
    }"
  >
    <div v-if="showSidebar" style="min-width: 250px">
      <slot name="sidebar" />
    </div>

    <div class="flex-grow-1">
      <slot name="content" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, Ref, watch, computed, onMounted } from 'vue';
import { useGlobalStore } from '@/stores/global';
import DarkModeToggle from './DarkModeToggle.vue';
import Button from 'primevue/button';
import { dataProvider } from '@/services/data';
import { router } from '@/router';
const $global = useGlobalStore();

const slots = defineSlots<{
  sidebar: any;
  content: any;
  logo: any;
  appname: any;
  start: any;
  center: any;
  'before-end': any;
  end: any;
  submenu: any;
}>();

const props = defineProps({
  hideSidebar: {
    type: Boolean,
    default: false,
  },
});

// mobile mode depends on window size

const mobile = ref(window.innerWidth < 768);

onMounted(() => {
  const onResize = () => {
    mobile.value = window.innerWidth < 768;
  };

  window.addEventListener('resize', onResize);

  return () => {
    window.removeEventListener('resize', onResize);
  };
});

// sidemenu
const showSidebar = computed(() => {
  if (mobile.value) return false;
  if (props.hideSidebar) return false;
  return true;
});

const showEndMenu = ref(false);

const colorMode = computed(() => {
  return $global.mode;
});

watch(
  () => colorMode.value,
  (newVal) => {
    console.log('mode changed', newVal);
    if (newVal === 'light') {
      toggleToLight();
      $global.mode = 'light';
    } else {
      toggleToDark();
      $global.mode = 'dark';
    }
  },
);

// const fontSize = ref(15);
// const increaseFontSize = (cnt = 1) => {
//     if (fontSize.value >= 24) return;
//     fontSize.value += cnt;
//     document.getElementsByTagName('html')[0].style.fontSize = fontSize.value + 'px';
// }
// const decreaseFontSize = (cnt = 1) => {
//     if (fontSize.value <= 8) return;
//     fontSize.value -= cnt;
//     document.getElementsByTagName('html')[0].style.fontSize = fontSize.value + 'px';
// }

const theme: Ref<'md-light-indigo' | 'md-dark-indigo'> = ref('md-light-indigo');

const loadStylesheet = (themeName: 'md-light-indigo' | 'md-dark-indigo') => {
  // Remove the existing theme if it's present
  const existingTheme = document.getElementById('theme-toggle');
  if (existingTheme) {
    existingTheme.remove();
  }
  // update theme
  theme.value = themeName;

  // Create a new link element for the desired theme
  const link = document.createElement('link');
  link.id = 'theme-toggle';
  link.rel = 'stylesheet';
  // /themes/md-light-indigo.css
  link.href = `./themes/${themeName}.css`; // adjust the path if needed
  // add to header at first position to not overwrite other styles
  document.head.insertBefore(link, document.head.firstChild);
};

const toggleToDark = () => {
  $global.saveUserSettings();
  loadStylesheet('md-dark-indigo');
  // PV.changeTheme("md-light-indigo", "md-dark-indigo", "theme-toggle", () => { });
};
const toggleToLight = () => {
  $global.saveUserSettings();
  loadStylesheet('md-light-indigo');
  // PV.changeTheme("md-dark-indigo", "md-light-indigo", "theme-toggle", () => { });
};

$global.getUserSettings();

defineExpose({
  closeSidebar: () => {
    showEndMenu.value = false;
  },
});

const logout = async () => {
  await dataProvider.logout();
  router.push('/login');
};
</script>

<style lang="scss">
html {
  /* initial value */
  font-size: 15px;
}

body {
  margin: 0px !important;
}

#toolbar-desktop {
  background-color: #afafaf;
}

div .darkmode {
  background-color: #252525;
  color: rgb(210, 210, 210);
}

div .lightmode {
  background-color: white;
  color: rgb(87 87 87);
}

ul.desktop-submenu-list > li {
  float: left;
  font-size: 0.9rem;
  padding-left: 5px;
}

ul.mobile-submenu-list {
  padding-left: 0px !important;
  font-size: 1.1rem;
  cursor: pointer;
  margin-top: 10px;
}

ul.mobile-submenu-list > li {
  padding-top: 10px;
  padding-bottom: 10px;
}

.app-layout {
  &__content {
    display: grid;
    gap: 1rem;

    overflow: auto;

    width: 100%;
    grid-template-columns: max(25%, 250px) 1fr;

    &:not(.showSidebar) {
      grid-template-columns: 100%;
    }

    @media screen and (max-width: 768px) {
      grid-template-columns: 100%;
    }
  }
}
</style>
