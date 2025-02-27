<template>
  <!-- Dialog to upload new media -->
  <Dialog
    v-model:visible="uploadDialogControl.show"
    modal
    header="Add image/video"
    :style="{ width: '40vw' }"
  >
    <template #default>
      <div class="p-1">
        <div v-if="uploadDialogControl.mode === 'sub'">
          <label>Select a language</label>
          <Dropdown
            :options="missingLanguages"
            option-label="name"
            option-value="code"
            placeholder="Select a language"
            class="w-full mt-2"
            v-model="languageToAdd"
            :disabled="$global.$state.requestPending"
          />
        </div>
        <FileUpload
          class="mt-4"
          mode="basic"
          accept="video/*, image/*"
          :maxFileSize="1000000"
          customUpload
          @uploader="upload($event)"
        />
      </div>
    </template>
  </Dialog>

  <Toolbar>
    <template #start>
      <div class="flex flex-row gap-1">
        <SplitButton
          v-if="!_documentId"
          @click="uploadDialogControl = { show: true, mode: 'main' }"
          label="Add"
          icon="fa-solid fa-plus"
          :model="menuAdd"
        />
        <Button
          v-if="!_documentId"
          @click="getMediaWithoutDocument"
          v-tooltip="'Get all items without a document reference'"
          icon="fa-solid fa-book-bookmark"
          class="border-none ml-1"
        />
      </div>
    </template>
    <template #end>
      <div class="flex flex-row gap-1">
        <ConfirmPopup />
        <Button
          v-tooltip="'Re-Upload media'"
          icon="fa-solid fa-repeat"
          class="border-none ml-1"
          @click="uploadDialogControl = { show: true, mode: 'replace' }"
          v-show="selection && Object.keys(selection).length > 0"
        />
      </div>
      <div class="flex flex-row gap-1">
        <Button
          v-tooltip="'Delete media'"
          icon="fa-solid fa-trash"
          class="border-none ml-1"
          @click="deleteSelected($event)"
          v-show="selection && Object.keys(selection).length > 0"
        />
      </div>
      <div class="flex flex-row gap-1">
        <Button
          icon="fa-solid fa-times"
          class="border-none ml-1"
          @click="closeDocument"
          v-if="_documentId"
          v-tooltip="'Show all media and close ' + documentId"
        />
      </div>
    </template>
  </Toolbar>

  <div id="media-browser-main">
    <div
      v-if="$global.$state.isLoading || $global.$state.requestPending"
      class="flex justify-content-center flex-wrap mt-5"
    >
      <ProgressSpinner />
    </div>
    <div
      v-else-if="$media.media.length === 0"
      class="flex justify-content-center flex-wrap mt-5"
    >
      <h3>No media found</h3>
    </div>
    <div v-else class="grid w-full mt-1" style="height: calc(100vh - 105px)">
      <div class="col-6">
        <DataTable
          :value="$media.media"
          @row-select="selectItem($event)"
          selection-mode="single"
          v-model:selection="selection"
        >
          <Column field="id" header="ID"></Column>
          <Column field="type" header="Type"></Column>
          <!-- <Column field="url" header="URL"></Column>
        <Column field="name" header="Name"></Column> -->
        </DataTable>
      </div>
      <div class="col-6">
        <div v-if="itemSelected">
          <div
            class="flex flex-row flex-wrap card-container blue-container ml-2 mr-2 mb-2"
          >
            <Button
              icon="fa-solid fa-plus"
              @click="uploadDialogControl = { show: true, mode: 'sub' }"
              :disabled="missingLanguages.length < 1"
            ></Button>
            <Dropdown
              v-model="selectedLanugage"
              option-label="name"
              option-value="code"
              :options="subLanguages"
              class="ml-1 flex-auto"
              :disabled="false"
              @change="switchLanguage"
            />
          </div>
          <MediaViewer :id="itemSelected.id" :type="itemSelected.type" />
        </div>
        <div v-else>
          <h4 class="w-full text-center">No item selected</h4>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import ProgressSpinner from 'primevue/progressspinner';
import Button from 'primevue/button';
import SplitButton from 'primevue/splitbutton';
import Dropdown from 'primevue/dropdown';
import Toolbar from 'primevue/toolbar';
import ConfirmPopup from 'primevue/confirmpopup';
import { useGlobalStore } from '../stores/global';
import { useConfirm } from 'primevue/useconfirm';
import { useMediaStore } from './../stores/media';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import { Medium } from './../services/data/types';
import MediaViewer from './../components/MediaViewer.vue';
import Dialog from 'primevue/dialog';
import FileUpload from 'primevue/fileupload';
import { dataProvider } from './../services/data';
import { error, info } from './../services/toast';
import {
  LanguageItem,
  mapLangCodesToLanguageItems,
  getMissingLanguagesItems,
  baseLanguage,
} from './../services/language/languageService';

const $media = useMediaStore(); // media store
const confirm = useConfirm(); // confirm dialog
const $global = useGlobalStore(); // global store

const uploadDialogControl = ref({
  show: false,
  mode: <'main' | 'sub' | 'replace'>'main',
}); // control: dialog for uploading a new file
const selection = ref<any>(null);
const languageToAdd = ref(baseLanguage); // dropdown: sub-language to add

// props
const props = defineProps<{
  documentId?: string;
}>();
const _documentId = ref<string | null>(props.documentId ?? null);

// "add" split-button
const menuAdd = [
  {
    label: 'Add smart video',
    command: () => window.open('/#/smart-video-dashboard', '_blank'),
  },
  {
    label: 'Upload mage/video',
    command: () => (uploadDialogControl.value = { show: true, mode: 'main' }),
  },
];

/**
 * select item
 */
const itemSelected = ref<Medium | null>(null);
const subItems = ref<Medium[]>([]);
const baseItem = ref<Medium | null>(null);
const subLanguages = ref<LanguageItem[]>([]);
const missingLanguages = ref<LanguageItem[]>([]);
const selectedLanugage = ref(baseLanguage);

const selectItem = async (event: any) => {
  itemSelected.value = event.data;
  if (!itemSelected.value?.id) return;

  // check for items with originId = documentId
  subItems.value = await dataProvider.getMediums({
    originId: itemSelected.value.id,
  });
  baseItem.value = itemSelected.value;

  // set to base language
  selectedLanugage.value = baseLanguage;

  // get all languages from subItems
  const langCodes = subItems.value.map((item) => item.langCode);
  // get missing languages
  missingLanguages.value = getMissingLanguagesItems(langCodes);
  if (missingLanguages.value.length > 0) {
    languageToAdd.value = missingLanguages.value[0].code;
  }
  subLanguages.value = mapLangCodesToLanguageItems([
    ...langCodes,
    baseLanguage,
  ]);
};

/**
 * change the language
 */
const switchLanguage = async () => {
  // check if selectedLanguage is baseLanguage
  if (selectedLanugage.value === baseLanguage) {
    itemSelected.value = baseItem.value;
    return;
  }
  // get element with langCode
  const item = subItems.value.find(
    (item) => item.langCode === selectedLanugage.value,
  );
  if (item) {
    itemSelected.value = item;
  }
};

/**
 * Upload a new file
 */
const upload = async (event: any) => {
  $global.$state.requestPending = true;
  try {
    const file = event.files[0];

    // depending on mode, use selected language from dialog, selected language from sub-menu or base language
    if (uploadDialogControl.value.mode === 'main') {
      const media = await dataProvider.addMedium(file, languageToAdd.value);
      console.log('uploaded file', media);
      info('New File uploaded successfully');
    }
    // upload new sub-language for media
    else if (uploadDialogControl.value.mode === 'sub' && baseItem.value?.id) {
      const media = await dataProvider.addMedium(
        file,
        languageToAdd.value,
        undefined,
        baseItem.value.id,
      );
      console.log('uploaded file', media);
      info('New language depending File uploaded successfully');
      // remove langCode from missingLanguages
      missingLanguages.value = missingLanguages.value.filter(
        (item) => item.code !== languageToAdd.value,
      );
      // add langCode to subLanguages
      subLanguages.value.push(
        mapLangCodesToLanguageItems([languageToAdd.value])[0],
      );
    }
    // replace media
    else if (
      uploadDialogControl.value.mode === 'replace' &&
      itemSelected.value?.id
    ) {
      const media = await dataProvider.updateMedium(
        itemSelected.value.id,
        file,
      );
      console.log('updated file', media);
      info('File updated successfully');
    }

    uploadDialogControl.value = { show: false, mode: 'main' };
    await init();
  } catch (e) {
    error(e + '');
  }
  $global.$state.requestPending = false;
};

/**
 * Delete the selected document.
 */
const deleteSelected = (event: any) => {
  confirm.require({
    target: event.currentTarget,
    message: 'Are you sure you want to proceed?',
    icon: 'fa-solid fa-trash',
    accept: async () => {
      if (itemSelected.value?.id == null) return;
      await dataProvider.dropMedium(itemSelected.value.id).catch((e) => {
        error(e + '');
      });
      await init();
      console.log('deleteSelected', selection.value);
    },
  });
};

/**
 * Close the current document.
 */
const closeDocument = async () => {
  _documentId.value = null;
  selection.value = {};
  itemSelected.value = null;
  await init();
};

/**
 * Get all media without document reference
 */
const getMediaWithoutDocument = async () => {
  $global.$state.isLoading = true;
  await $media.getMediaWithoutDocument();
  $global.$state.isLoading = false;
  selection.value = {};
  itemSelected.value = null;
};

/**
 * Get all media
 */
const init = async () => {
  $global.$state.isLoading = true;
  await $media.initialize(_documentId.value ?? undefined);
  $global.$state.isLoading = false;
  selection.value = {};
  itemSelected.value = null;
};

// App Start
onMounted(async () => {
  await init();
});
</script>
