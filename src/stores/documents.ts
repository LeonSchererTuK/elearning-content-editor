import { defineStore } from 'pinia';
import { dataProvider } from '../services/data';
import { DocumentItem, DocumentTreeItem } from '../services/data/types';

const DATASOURCE: string = import.meta.env.VITE_DOCUMENT_DATASOURCE ?? 'mock';

console.log('DOCUMENT_DATASOURCE', DATASOURCE);

interface DocumentState {
  documentSource: null | string;
  documentTree: DocumentTreeItem[];
  documentsFlat: DocumentItem[];
}

export const useDocumentStore = defineStore('documents', {
  state: () =>
    ({
      documentSource: null,
      documentTree: [],
      documentsFlat: [],
    }) as DocumentState,

  actions: {
    async initialize() {
      this.$state.documentSource = DATASOURCE;
      const data = await dataProvider.getDocuments();
      this.$state.documentTree = data.tree;
      this.$state.documentsFlat = data.list;
    },

    async updateDocument(document: DocumentItem) {
      await dataProvider.updateDocument(document);

      // update current tree
      let item = this.$state.documentsFlat.find(
        (item) => item.id === document.id,
      );

      if (item) {
        item = document;
      }
    },

    async dropDocument(id: string) {
      await dataProvider.dropDocument(id);
      await this.initialize(); // TODO: optimize
    },

    async addDocument(document: DocumentItem) {
      await dataProvider.addDocument(document);
      // update current tree
      await this.initialize(); // TODO: optimize
    },

    async getDocument(id: string): Promise<DocumentItem> {
      return await dataProvider.getDataForDocument(id);
    },

    async dropNode(id: string) {
      const node = this.$state.documentsFlat.find((item) => item.id === id);

      if (!node) {
        console.error(`Node with id ${id} not found`);
        return;
      }

      const getNodes = (node: DocumentItem | DocumentTreeItem): string[] => {
        if (node.type === 'folder' && 'children' in node && node.children) {
          return [node.id, ...node.children.flatMap(getNodes)];
        } else {
          return [node.id];
        }
      };

      const nodes = getNodes(node);

      await dataProvider.dropNodes(nodes);

      // update current tree
      await this.initialize(); // TODO: optimize
    },
  },
});
