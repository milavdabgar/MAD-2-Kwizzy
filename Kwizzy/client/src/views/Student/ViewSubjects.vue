<template>
  <div>
    <div class="absolute sm:top-6 top-16 bg-white">
      <div class="sm:w-[450px] w-[300px]">
        <SearchBar @search="handleSearch" placeholder="Search subjects..." />
      </div>
    </div>

    <div class="mb-6 sm:mt-4 mt-14 flex flex-col gap-1">
      <h1 class="text-4xl font-bold">Subjects</h1>

      <p>
        Explore a variety of subjects and choose the ones you want to practice.
      </p>
    </div>
    <SubjectCard
      :subjects="filteredSubjects"
      :loading="subjectStore.isLoading"
    />
  </div>
</template>
<script setup>
import { ref, onMounted, computed } from "vue";
import { useSubjectStore } from "@/stores/subjectStore";
const subjectStore = useSubjectStore();
import SearchBar from "../../components/Admin/SearchBar.vue";
import SubjectCard from "@/components/Student/SubjectCard.vue";

const props = defineProps({
  student: {
    type: Object,
    required: true,
  },
});

const searchQuery = ref("");

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

const student = ref(props.student);

onMounted(() => {
  subjectStore.fetchSubjects();
});
</script>
