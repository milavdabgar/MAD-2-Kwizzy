<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter, RouterLink } from "vue-router";
import "../../assets/font.css";
import logo from "../../assets/images/landing-page/white logo.png";
import axios from "axios";
const API_URL = import.meta.env.VITE_API_URL;
import Sidebar from "@/components/Admin/Sidebar.vue";
import EditSubject from "@/components/Admin/EditSubject.vue";
import AddChapter from "@/components/Admin/AddChapter.vue";
import EditChapter from "@/components/Admin/EditChapter.vue";
import SearchBar from "@/components/Admin/SearchBar.vue";
import Loader from "@/components/Loader.vue";
import { useToast } from "@/composables/useToast";
import { useSubjectStore } from "@/stores/subjectStore";

const subjectStore = useSubjectStore();

const toast = useToast();
const route = useRoute();
const router = useRouter();
const subjectId = route.params.id;
const subject = ref(null);
const chapters = ref([]);
const searchQuery = ref("");

const selectedChapter = ref(null);
const isAddChapterModalOpen = ref(false);
const isEditChapterModalOpen = ref(false);
const isEditSubjectModalOpen = ref(false);
const isLoading = ref(true);

const fetchSubjectDetails = async () => {
  try {
    isLoading.value = true;
    const token = localStorage.getItem("access_token");
    if (!token) throw new Error("No access token available");

    const response = await axios.get(`${API_URL}/subject/${route.params.id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    subject.value = {
      ...response.data,
      image: `${API_URL}/uploads/subjects/${response.data.subject_image}`,
    };
  } catch (error) {
    console.error("Error fetching subject details:", error);
  } finally {
    isLoading.value = false;
  }
};

const fetchChapters = async () => {
  try {
    isLoading.value = true;
    const token = localStorage.getItem("access_token");
    if (!token) throw new Error("No access token available");

    const response = await axios.get(`${API_URL}/chapter`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: { subject_id: subjectId },
    });
    chapters.value = response.data.chapters || [];
    console.log("Chapters:", chapters.value);
  } catch (error) {
    console.error("Error fetching subject details:", error);
  } finally {
    isLoading.value = false;
  }
};

const handleChapterCreated = (chapter) => {
  chapters.value.push(chapter);
  isAddChapterModalOpen.value = false;
};

const handleChapterUpdated = (updatedChapter) => {
  const index = chapters.value.findIndex(
    (chapter) => chapter.id === updatedChapter.id
  );
  if (index !== -1) {
    chapters.value[index] = updatedChapter; // Update the chapter in the array
  }
  isEditChapterModalOpen.value = false; // Close the edit modal
};

const handleSubjectUpdated = (updatedSubject) => {
  subject.value = {
    ...updatedSubject,
    image: `${API_URL}/uploads/subjects/${updatedSubject.subject_image}`,
  };
  console.log("Updated subject:", subject.value);
  isEditSubjectModalOpen.value = false;
  subjectStore.updateSubject(updatedSubject);
};

onMounted(() => {
  fetchSubjectDetails();
  fetchChapters();
});

const openEditModal = (chapter) => {
  selectedChapter.value = chapter;
  isEditChapterModalOpen.value = true;
};

const editSubject = (subject) => {
  isEditSubjectModalOpen.value = true;
};

const handleDeleteSubject = async (subjectId) => {
  if (!confirm("Are you sure you want to delete this subject?")) {
    return;
  }
  const success = await subjectStore.deleteSubject(subjectId);
  if (success) {
    router.push("/admin/dashboard");
  }
};

const deleteChapter = async (chapterId) => {
  try {
    const token = localStorage.getItem("access_token");
    if (!token) {
      toast.error("No access token available");
      return;
    }
    if (!confirm("Are you sure you want to delete this chapter?")) {
      return;
    }
    const response = await axios.delete(`${API_URL}/chapter/${chapterId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.data && response.status === 200) {
      toast.success("Chapter deleted successfully");
      chapters.value = chapters.value.filter(
        (chapter) => chapter.id !== chapterId
      );
    } else {
      throw new Error("Unexpected response from server");
    }
  } catch (error) {
    if (error.response) {
      toast.error(error.response.data.message || "Error deleting chapter");
    }
    await fetchChapters();
  }
};

const filteredChapters = computed(() => {
  if (!searchQuery.value) {
    return chapters.value;
  }

  return chapters.value.filter(
    (chapter) =>
      chapter.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      chapter.description
        .toLowerCase()
        .includes(searchQuery.value.toLowerCase())
  );
});

const handleSearch = (query) => {
  searchQuery.value = query;
};
</script>

<template>
  <Loader v-if="isLoading" />
  <Sidebar v-else>
    <header class="h-16 bg-white flex items-center justify-between gap-6 mb-2">
      <div class="flex items-center flex-1">
        <div class="flex-1 max-w-lg">
          <div class="relative">
            <SearchBar
              @search="handleSearch"
              placeholder="Search chapters..."
            />
          </div>
        </div>
      </div>

      <!-- Right Side Icons -->
      <div class="flex items-center">
        <div class="flex items-center gap-4">
          <img
            :src="logo"
            alt="User avatar"
            class="w-8 h-8 rounded-full mix-blend-difference"
          />
          <span class="text-sm font-medium text-gray-700">Admin</span>
        </div>
      </div>
    </header>
    <!-- Breadcrumbs -->
    <div class="flex items-center gap-2 text-sm mb-6">
      <router-link
        to="/admin"
        class="text-gray-500 hover:text-black sohne-mono"
      >
        Subjects
      </router-link>
      <span class="text-gray-500">/</span>
      <span class="font-medium sohne-mono">{{ subject?.name }}</span>
    </div>

    <!-- Subject Header -->
    <div
      class="flex items-start flex-col sm:flex-row sm:gap-8 gap-4 mb-8 sm:px-0 px-2"
    >
      <img
        :src="subject?.image"
        :alt="subject?.name"
        class="sm:w-[180px] sm:h-[180px] w-screen h-[150px] rounded-xl object-cover"
      />
      <div>
        <h1 class="text-4xl font-bold mb-2 magnetic">{{ subject?.name }}</h1>
        <p class="text-gray-600 max-w-xl mb-2">{{ subject?.description }}</p>
        <div class="flex items-start gap-4 mb-2">
          <button
            @click="editSubject(subject)"
            class="text-sm text-gray-500 hover:text-[#0000ff] transition-colors sohne-mono"
          >
            [Edit]
          </button>
          <button
            @click="handleDeleteSubject(subject.id)"
            class="text-sm text-gray-500 rounded-lg hover:text-[#ff0a0a] transition-colors sohne-mono"
          >
            [Delete]
          </button>
        </div>
        <button
          @click="isAddChapterModalOpen = true"
          class="flex items-center gap-2 px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-900 hover:scale-95 transition-all duration-200 ease-linear"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 4v16m8-8H4"
            />
          </svg>
          Add Chapter
        </button>
      </div>
    </div>
    <!-- Chapters Table -->
    <div>
      <p class="text-xl sohne font-bold mb-4">
        Total Chapters:
        <span class="font-bold">{{ filteredChapters.length }}</span>
      </p>
      <div class="px-2">
        <table class="w-full chapters">
          <thead>
            <tr class="text-left sm:text-sm text-xs border-b-2 border-black">
              <th>Chapter Name</th>
              <th class="sm:table-cell hidden">Description</th>
              <th class="sm:block hidden">Quizzes</th>
              <th class="text-right px-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="chapters.length === 0">
              <td colspan="4" class="py-4 text-center sohne text-gray-500">
                No chapters found. Add first chapter!
              </td>
            </tr>
            <tr
              v-for="chapter in filteredChapters"
              :key="chapter.id"
              class="border-b text-sm border-black"
            >
              <RouterLink
                :to="`/admin/subject/${subject.id}/chapter/${chapter.id}`"
              >
                <td class="py-2 block">
                  ▞ &nbsp;<span class="hover:text-[#0000ff]">{{
                    chapter.name
                  }}</span>
                </td>
              </RouterLink>

              <td class="py-2 sm:table-cell hidden">
                {{ chapter.description }}
              </td>
              <td class="py-2 sm:block hidden">
                {{ chapter.total_quizzes || 0 }}
              </td>
              <td class="py-2">
                <div class="flex items-center justify-end gap-2 px-2">
                  <button
                    @click="openEditModal(chapter)"
                    class="py-[2px] px-1 text-gray-600 hover:text-[#0000ff] sohne-mono text-[12px] border-dotted border border-gray-400 link-hover"
                  >
                    EDIT
                  </button>
                  <button
                    @click="deleteChapter(chapter.id)"
                    class="py-[2px] px-1 text-gray-600 hover:text-red-600 sohne-mono text-[12px] border-dotted border border-gray-400 link-hover"
                  >
                    DELETE
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Edit Subject Modal (create a separate component for this) -->
    <EditSubject
      v-if="isEditSubjectModalOpen"
      :is-open="isEditSubjectModalOpen"
      :subject="{
        ...subject,
        subject_image: subject.subject_image,
      }"
      @close="isEditSubjectModalOpen = false"
      @update="handleSubjectUpdated"
    />

    <!-- Add Chapter Modal (create a separate component for this) -->
    <AddChapter
      v-if="isAddChapterModalOpen"
      :is-open="isAddChapterModalOpen"
      :subject-id="route.params.id"
      :subject-name="subject.name"
      @close="isAddChapterModalOpen = false"
      @create="handleChapterCreated"
    />

    <!-- Edit Chapter Modal (create a separate component for this) -->
    <EditChapter
      v-if="isEditChapterModalOpen"
      :is-open="isEditChapterModalOpen"
      :subject-id="route.params.id"
      :subject-name="subject.name"
      :chapter="selectedChapter"
      @close="isEditChapterModalOpen = false"
      @update="handleChapterUpdated"
    />
  </Sidebar>
</template>

<style>
* {
  cursor: none;
}
.sohne {
  font-family: sohne;
}
.sohne-mono {
  font-family: sohne-mono;
  text-transform: uppercase;
}

table th {
  font-family: sohne-mono;
  text-transform: uppercase;
}
table td,
table td span {
  font-family: monospace;
  font-size: 18px;
  letter-spacing: -0.6px;
}

.chapters tbody tr {
  transition: all 0.15s ease;
}

.chapters tbody tr:hover {
  background-color: #f0f0ff;
}

button {
  cursor: none;
}
</style>
