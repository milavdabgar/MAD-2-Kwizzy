<script setup>
import Sidebar from "@/components/Admin/Sidebar.vue";
import SubjectCard from "@/components/Admin/SubjectCard.vue";
import { ref, onMounted, computed } from "vue";
import CreateSubject from "@/components/Admin/AddSubject.vue";
import SearchBar from "@/components/Admin/SearchBar.vue";
import logo from "../../assets/images/landing-page/white logo.png";
import { useSubjectStore } from "@/stores/subjectStore";
const subjectStore = useSubjectStore();
const searchQuery = ref("");
const isCreateModalOpen = ref(false);

const filteredSubjects = computed(() => {
  if (!searchQuery.value) return subjectStore.allSubjects;

  const query = searchQuery.value.toLowerCase();
  return subjectStore.allSubjects.filter(
    (subject) =>
      subject.name.toLowerCase().includes(query) ||
      subject.description.toLowerCase().includes(query)
  );
});

const handleSearch = (query) => {
  searchQuery.value = query;
};

const handleCreateSubject = async () => {
  subjectStore.invalidateCache();
  await subjectStore.fetchSubjects(true);
  isCreateModalOpen.value = false;
};

onMounted(() => {
  subjectStore.fetchSubjects();
});
</script>

<template>
  <div>
    <Sidebar>
      <header
        class="h-16 bg-white flex items-center justify-between sm:pr-0 pr-3"
      >
        <div class="flex items-center flex-1">
          <div class="flex-1 max-w-lg">
            <div class="relative">
              <SearchBar
                @search="handleSearch"
                placeholder="Search subjects..."
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
      <div class="mb-6 mt-4 sm:px-0 px-3">
        <h1 class="text-4xl font-bold">Subjects</h1>
        <p>Manage and organize the subjects</p>
      </div>

      <SubjectCard
        :subjects="filteredSubjects"
        :loading="subjectStore.isLoading"
      />
      <CreateSubject
        :is-open="isCreateModalOpen"
        @close="isCreateModalOpen = false"
        @create="handleCreateSubject"
      />
      <!-- Floating Add Subject Button -->
      <button
        @click="isCreateModalOpen = true"
        class="fixed bottom-6 sm:right-6 right-[calc(50%-80px)] z-30 flex items-center gap-2 px-4 py-3 bg-white hover:bg-black text-black hover:text-white font-semibold border-2 border-black rounded-full shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300"
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
        <span>Add Subject</span>
      </button>
    </Sidebar>
  </div>
</template>
