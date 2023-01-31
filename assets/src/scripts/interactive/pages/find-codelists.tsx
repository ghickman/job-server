import { Form, Formik } from "formik";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as Yup from "yup";
import { Button } from "../components/Button";
import CodelistButton from "../components/Button/CodelistButton";
import CodelistSearch from "../components/CodelistSearch";
import Fieldset from "../components/Fieldset";
import FormDebug from "../components/FormDebug";
import InputError from "../components/InputError";
import RadioButton from "../components/RadioButton";
import { frequency } from "../data/form-fields";
import { codelistSchema } from "../data/schema";
import { useFormStore, usePageData } from "../stores";
import { FormDataTypes } from "../types";

function FindCodelists() {
  const formData: FormDataTypes = useFormStore((state) => state.formData);
  const { pageData } = usePageData.getState();
  const [secondCodelist, setSecondCodelist]: [boolean, Function] = useState(
    !!formData.codelist1
  );
  const navigate = useNavigate();

  const validationSchema = Yup.object({
    codelist0: codelistSchema(pageData),
    codelist1: secondCodelist
      ? codelistSchema(pageData).test(
          "compare_codelists",
          "Codelists cannot be the same, please change one codelist",
          (value: string, testContext: Yup.TestContext) => {
            if (
              Object.entries(testContext.parent.codelist0).toString() ===
              Object.entries(value).toString()
            ) {
              return false;
            }

            return true;
          }
        )
      : null,
    frequency: Yup.string()
      .oneOf(frequency.items.map((item) => item.value))
      .required("Select a frequency"),
  });

  return (
    <Formik
      initialValues={{
        codelist0: formData.codelist0 || "",
        codelist1: formData.codelist1 || undefined,
        frequency: formData.frequency || "",
      }}
      onSubmit={(values, actions) => {
        actions.validateForm().then(() => {
          useFormStore.setState({ formData: { ...formData, ...values } });
          if (secondCodelist) {
            return navigate("/build-query");
          }
          return navigate("/review-query");
        });
      }}
      validateOnMount
      validationSchema={validationSchema}
    >
      {({ errors, isValid, touched }) => (
        <Form>
          <CodelistSearch id={0} label="Select a codelist" />

          {secondCodelist ? (
            <CodelistSearch id={1} label="Select another codelist" />
          ) : null}

          <CodelistButton
            secondCodelist={secondCodelist}
            setSecondCodelist={setSecondCodelist}
          />

          <Fieldset legend={frequency.label} name="frequency">
            {frequency.items.map((item) => (
              <RadioButton
                key={item.value}
                id={item.value}
                label={item.label}
                name="frequency"
                value={item.value}
              />
            ))}
            {errors.frequency && touched.frequency ? (
              <InputError>{errors.frequency}</InputError>
            ) : null}
          </Fieldset>

          <Button className="mt-6" disabled={!isValid} type="submit">
            Next
          </Button>

          <FormDebug />
        </Form>
      )}
    </Formik>
  );
}

export default FindCodelists;
