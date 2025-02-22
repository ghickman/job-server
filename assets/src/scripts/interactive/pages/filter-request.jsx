import { Form, Formik } from "formik";
import { Redirect, useLocation } from "wouter";
import * as Yup from "yup";
import { AlertForm } from "../components/Alert";
import Button from "../components/Button";
import Checkbox from "../components/Checkbox";
import Fieldset from "../components/Fieldset";
import HintText from "../components/HintText";
import InputError from "../components/InputError";
import RadioButton from "../components/RadioButton";
import { useFormData } from "../context";
import { demographics, filterPopulation } from "../data/form-fields";
import { useRequiredFields } from "../utils";

function FilterRequest() {
  const [, navigate] = useLocation();
  const { formData, setFormData } = useFormData();

  if (useRequiredFields(["codelistA", "codelistB", "timeOption"])) {
    return <Redirect to="" />;
  }

  const validationSchema = Yup.object().shape({
    filterPopulation: Yup.string()
      .oneOf(filterPopulation.items.map((item) => item.value))
      .required("Select a filter for the population"),
    demographics: Yup.array()
      .of(Yup.string().oneOf(demographics.items.map((item) => item.value)))
      .min(0)
      .max(demographics.items.length),
  });

  const initialValues = {
    filterPopulation: formData.filterPopulation || "",
    demographics: formData.demographics || [],
  };

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          setFormData({ ...formData, ...values });
          navigate("analysis-information");
        });
      }}
      validateOnMount
      validationSchema={validationSchema}
    >
      {({ errors, isValid, touched }) => (
        <Form className="flex flex-col gap-y-8">
          <AlertForm />
          <h1 className="text-4xl font-bold">Set report filters</h1>

          <Fieldset legend={filterPopulation.label}>
            {filterPopulation.items.map((item) => (
              <RadioButton
                key={item.value}
                id={item.value}
                label={item.label}
                name="filterPopulation"
                value={item.value}
              />
            ))}
            {errors.filterPopulation && touched.filterPopulation ? (
              <InputError>{errors.filterPopulation}</InputError>
            ) : null}
          </Fieldset>

          <Fieldset legend={demographics.label}>
            <HintText>
              <p>
                These should only be selected if they align with your approved
                project purpose. Selecting more options will increase report
                processing time.
              </p>
            </HintText>
            {demographics.items.map((item) => (
              <Checkbox
                key={item.value}
                id={item.value}
                label={item.label}
                name="demographics"
                value={item.value}
              />
            ))}
            {errors.demographics && touched.demographics ? (
              <InputError>Select one or more demographics</InputError>
            ) : null}
          </Fieldset>

          <div className="flex flex-row w-full gap-2 mt-10">
            <Button disabled={!isValid} type="submit">
              Next
            </Button>
          </div>
        </Form>
      )}
    </Formik>
  );
}

export default FilterRequest;
